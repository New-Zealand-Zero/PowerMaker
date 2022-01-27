#!/usr/bin/env python3

# Importing configeration
from datetime import time
import config
import pymysql
import config

# Importing supporting functions
from powermakerfunctions import *

# Importing modules
import logging # flexible event logging
import math # mathematical functions
from time import sleep  # To add delay
import matplotlib.pyplot as plt
import numpy as np


rates=[]
spot_prices = []


i=0.00
while(i<=1):
    spot_prices.append(i)
    if (i<config.IMPORT_QUANTILE) :
        rates.append(calc_charge_rate(i, config.IMPORT_QUANTILE, 0))
    elif(i>config.EXPORT_QUANTILE):
        rates.append(calc_discharge_rate(i, config.EXPORT_QUANTILE, 1))
    else:
        rates.append(0)
    i+=0.01


print(rates)

plt.plot(spot_prices,rates)
plt.show()
# plt.xlabel('Record')
# plt.ylabel('Spot Price')
# plt.title('Last 4 Hours Spot Price')

# normalized = np.linalg.norm(spot_prices)
# plt.hist(normalized, 10)
# plt.show()


