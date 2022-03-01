#!/usr/bin/env python3

import config
import pymysql
from powermakerfunctions import create_db_connection

# Connect to the database
conn = create_db_connection()   
c = conn.cursor()


# Create tables
c.execute(
    "ALTER TABLE DataPoint ADD COLUMN SuggestedIE INT ;"
)

conn.commit()
c.close()
conn.close()