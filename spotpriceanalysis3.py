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
c.execute("SELECT spotprice, actualIE from DataPoint where timestamp >= DATE_SUB(NOW(),INTERVAL 5 DAY)")
result = c.fetchall()
c.close()  
conn.close()

points = []
spot_prices = []
actual_IE = []

x=0
for i in result:
    x += 1
    points.append(x)
    spot_prices.append(i[0])
    actual_IE.append(i[1])

mean = np.mean(spot_prices)
sigma = np.std(spot_prices)
 
print("mean :", mean)
print("SD :", sigma)

print("1-sigma : ", mean - sigma, mean + sigma )
print("2-sigma : ", mean - 2 * sigma, mean + 2 * sigma )
print("3-sigma : ", mean - 3 * sigma, mean + 3 * sigma )

print("min",np.min(spot_prices))
print("lower quartile", np.quantile(spot_prices,0.25))
print("median :",np.median(spot_prices))
print("upper quartile", np.quantile(spot_prices,0.75))
print("max",np.max(spot_prices))

plt.hist(spot_prices, 10)
plt.show()

# normalized = np.linalg.norm(spot_prices)
# plt.hist(normalized, 10)
# plt.show()


