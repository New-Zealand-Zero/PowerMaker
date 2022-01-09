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
import numpy as np 

# Log to file in production on screen for test
if (config.PROD):
    logging.basicConfig(filename='io.log', level=logging.INFO, format='%(asctime)s %(message)s')
else:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s TEST %(message)s') 

# Connect to the database.
import pymysql
conn = pymysql.connect(
    db=config.DATABASE,    
    user=config.USER,
    passwd=config.PASSWD,
    host='localhost')
c = conn.cursor()

min_exp_value = 0
max_exp_value = 7
avg_spot_price= 100

print()
print("min_exp_value=", np.exp(min_exp_value), " ", "max_exp_value=", np.exp(max_exp_value))

multiplier = config.IE_MAX_RATE/np.exp(max_exp_value) 
print("multiplier=", multiplier)
print()

def calc_discharge_rate(spot_price):
    
    margin = spot_price - avg_spot_price

    print("margin=", margin)

    scaled_margin = np.interp(margin, [config.MARGIN_MIN , config.MARGIN_MAX],[config.MIN_EXP_VALUE, config.MAX_EXP_VALUE])
    
    scaled_margin_exp = np.exp(scaled_margin)
    print("scaled_margin=", scaled_margin," ", "scaled_margin_exp=",scaled_margin_exp)
  
    discharge_rate = config.IE_MIN_RATE + (scaled_margin_exp*multiplier)
    print("discharge_rate=",discharge_rate)

calc_discharge_rate(110)
calc_discharge_rate(120)
calc_discharge_rate(130)
calc_discharge_rate(140)
calc_discharge_rate(150)


# def calc_discharge_rate(spot_price):
    
#     margin = spot_price - avg_spot_price

#     print("margin=", margin)

#     scaled_margin = np.interp(margin, [config.MARGIN_MIN , config.MARGIN_MAX],[min_exp_value, max_exp_value])
    
#     scaled_margin_exp = np.exp(scaled_margin) - np.exp(min_exp_value)
#     print("scaled_margin=", scaled_margin," ", "scaled_margin_exp=",scaled_margin_exp)
  
#     discharge_rate = config.IE_MIN_RATE + (scaled_margin_exp*multiplier)
#     print("discharge_rate=",discharge_rate)