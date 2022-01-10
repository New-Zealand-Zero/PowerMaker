#!/usr/bin/env python3

# Importing configeration
from datetime import time
import config

# Importing supporting functions
from powermakerfunctions import *

# Importing modules
import logging # flexible event logging
import math # mathematical functions
from time import sleep  # To add delay
import matplotlib.pyplot as plt


# Connect to the database.
import pymysql
conn = pymysql.connect(
    db=config.DATABASE,    
    user=config.USER,
    passwd=config.PASSWD,
    host='localhost')
c = conn.cursor()

c.execute("SELECT * from DataPoint")
result = c.fetchall()

points = []
spot_prices = []
  
for i in result:
    points.append(i[0])
    spot_prices.append(i[1])


print(points)
print(spot_prices)

c.close()
conn.close()
 
# plotting the points
plt.plot(points, spot_prices)
 
# naming the x axis
plt.xlabel('Record')
# naming the y axis
plt.ylabel('Spot Price')
 
# giving a title to my graph
plt.title('Spot Price over time')
 
# function to show the plot
plt.show()