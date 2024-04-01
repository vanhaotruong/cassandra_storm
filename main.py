import pandas as pd
import os
from cassandra.cluster import Cluster
from uuid import uuid4
from datetime import datetime as dt

path = os.getcwd()
data_folder = path + "/data"

def preprocess_date(date_str):
    date_obj = dt.strptime(date_str, '%m/%d/%Y')
    return date_obj.strftime('%Y-%m-%d')

if __name__ == "__main__":
    
    insert_query = [
        """
            INSERT INTO iotsolution.bronze_turbine_sensor (id, angle, device_id, recorded_date, rpm, window)
            VALUES (%s, %s, %s, %s, %s, %s)
        """,
        """
            INSERT INTO iotsolution.bronze_weather_sensor (id, device_id, humidity, recorded_date, temperature, winddirection, window, windspeed)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
    ]
    
    data_file = ["raw_turbine_data.csv", "raw_weather_sensor.csv"]
    cluster = Cluster(['127.0.0.1'])
    session = cluster.connect()

    session.execute("""
    CREATE KEYSPACE IF NOT EXISTS iotsolution 
    WITH replication = { 'class': 'SimpleStrategy', 'replication_factor' : 1 };
    """)

    session.execute("""
    USE iotsolution;
    """)  

    session.execute("""
    CREATE TABLE IF NOT EXISTS bronze_turbine_sensor (
        id UUID PRIMARY KEY,
        recorded_date DATE,
        device_id TEXT,
        window TIMESTAMP,
        rpm FLOAT,
        angle FLOAT
    );
    """)

    session.execute("""
    CREATE TABLE IF NOT EXISTS bronze_weather_sensor (
        id UUID PRIMARY KEY,
        recorded_date DATE,
        device_id TEXT,
        window TIMESTAMP,
        temperature FLOAT,
        humidity FLOAT,
        windspeed FLOAT,
        winddirection TEXT
    );
    """)
    
    for query, file in zip(insert_query, data_file):
        try:
            df = pd.read_csv(f"{data_folder}/{file}")
            df['recorded_date'] = df['recorded_date'].apply(preprocess_date)

            for _, row in df.iterrows():
                data = tuple([uuid4(), *row])
                session.execute(query, data)
        except Exception as e:
            print(str(e))