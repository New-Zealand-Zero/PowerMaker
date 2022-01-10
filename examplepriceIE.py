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

avg_spot_price= 100

print()
print("min_exp_value=", np.exp(config.MIN_EXP_VALUE), " ", "max_exp_value=", np.exp(config.MAX_EXP_VALUE))

multiplier = (config.IE_MAX_RATE-config.IE_MIN_RATE)/np.exp(config.MAX_EXP_VALUE) 
print("multiplier=", multiplier)
print()

def calc_discharge_rate(spot_price):
    
    margin = spot_price - avg_spot_price

    print("margin=", margin)

    #linear scale margin to exp value
    scaled_margin = np.interp(margin, [config.MARGIN_MIN , config.MARGIN_MAX],[config.MIN_EXP_VALUE, config.MAX_EXP_VALUE])
    
    # apply the exp function to exp_value less the min
    scaled_margin_exp = np.exp(scaled_margin) - np.exp(config.MIN_EXP_VALUE)
    print("scaled_margin=", scaled_margin," ", "scaled_margin_exp=",scaled_margin_exp)
  
    #Scale exp function applied value to discharge rate 
    discharge_rate = config.IE_MIN_RATE + (scaled_margin_exp*multiplier)
    print("discharge_rate=",discharge_rate)

calc_discharge_rate(110)
calc_discharge_rate(120)
calc_discharge_rate(130)
calc_discharge_rate(140)
calc_discharge_rate(150)
