#!/usr/bin/env python3

import config
import pymysql
from powermakerfunctions import create_db_connection

# Connect to the database
conn = create_db_connection()   
c = conn.cursor()

# Drop tables
c.execute("DROP TABLE IF EXISTS DataPoint;")
c.execute("DROP TABLE IF EXISTS Config;")

# Create tables
c.execute(
    "CREATE TABLE DataPoint (RecordID int NOT NULL AUTO_INCREMENT, SpotPrice float, AvgSpotPrice float, SolarGeneration int, PowerLoad int, BatteryCharge Float, Status varchar(60), ActualIE Float, Timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, SuggestedIE INT, PRIMARY KEY (RecordID) );"
)
c.execute(
    "CREATE TABLE Config (ConfigID varchar(10), ConfigValue varchar(100));"
)
# Add first record to stop exception on avg calc and graph loading with no date
c.execute(f"INSERT INTO DataPoint (SpotPrice, AvgSpotPrice, SolarGeneration , PowerLoad , BatteryCharge , Status, ActualIE) VALUES (0, 0, 0, 0, 0, 'Dummy record', 0)")       
c.execute(f"INSERT INTO Config VALUES ('Override', 'N');")

conn.commit()
c.close()
conn.close()