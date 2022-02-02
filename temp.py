#!/usr/bin/env python3

# Importing configeration
from datetime import time
import config
import pymysql

# Importing supporting functions
from powermakerfunctions import *

# Importing modules
import logging # flexible event logging
import math # mathematical functions
from time import sleep  # To add delay
import matplotlib.pyplot as plt
import numpy as np

conn = create_db_connection()
c = conn.cursor()
c.execute("SELECT spotprice, timestamp from DataPoint where timestamp >= DATE_SUB(NOW(),INTERVAL 5 DAY)")
result = c.fetchall()
c.close()  
conn.close()

points = []
spot_prices = []
timestamp = []

x=0
for i in result:
    x += 1
    points.append(x)
    spot_prices.append(i[0])
    timestamp.append(i[1])

 
# Creating plot
plt.boxplot(spot_prices )
 
# show plot
plt.show()