#!/usr/bin/env python3

import config
import pymysql
from powermakerfunctions import create_db_connection

# Connect to the database.
conn = create_db_connection()   
c = conn.cursor()

# Drop and create tables
c.execute("DROP TABLE IF EXISTS DataPoint;")
c.execute(
    "CREATE TABLE DataPoint (RecordID int NOT NULL AUTO_INCREMENT, SpotPrice float, AvgSpotPrice float, SolarGeneration int, PowerLoad int, BatteryCharge Float, Status varchar(35), ActualIE Float, Timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (RecordID) );"
)
# Add first record to stop exception on avg calc and graph loading with no date
c.execute(f"INSERT INTO DataPoint (SpotPrice, AvgSpotPrice, SolarGeneration , PowerLoad , BatteryCharge , Status, ActualIE) VALUES (0, 0, 0, 0, 0, 'Dummy record', 0)")       

conn.commit()
c.close()
conn.close()