#!/usr/bin/env python3

import config

# Connect to the database.
import pymysql
conn = pymysql.connect(
    db=config.DATABASE,    
    user=config.USER,
    passwd=config.PASSWD,   
    host='localhost')
c = conn.cursor()

c.execute("DROP TABLE IF EXISTS DataPoint;")

# Create tables
c.execute(
    "CREATE TABLE DataPoint (RecordID int NOT NULL AUTO_INCREMENT, SpotPrice float, AvgSpotPrice float, SolarGeneration int, PowerLoad int, BatteryCharge Float, Status varchar(35), Timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (RecordID) );"
)

conn.commit()
c.close()
conn.close()