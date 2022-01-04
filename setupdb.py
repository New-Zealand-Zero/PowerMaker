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
    "CREATE TABLE DataPoint (RecordID int, Record datetime, AnalogMoisture int, SoilMoisture int, Humidity int);"
)
c.execute(
    "CREATE TABLE Forecast (ForecastID int, RecordID int, DateRecorded datetime, rain float);"
)

c.execute("CREATE TABLE config (id varchar(20), value varchar(20) )")
c.execute("ALTER TABLE `pihome`.`config` ADD UNIQUE `ID_Index` (`id`);")
c.execute("INSERT INTO config VALUES ('skip', -1)")
c.execute("INSERT INTO config VALUES ('version', 1)")
c.execute("INSERT INTO config VALUES ('override', 1)")
c.execute("INSERT INTO config VALUES ('temp', 20)")
c.execute("INSERT INTO config VALUES ('humidity', 1)")
c.execute("INSERT INTO config VALUES ('mintemp', 10)")
c.execute("INSERT INTO config VALUES ('heating', 'F')")
c.execute("INSERT INTO config VALUES ('watering', 'F')")

conn.commit()
c.close()
conn.close()