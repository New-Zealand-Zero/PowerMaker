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
from numpy import interp  # To scale values
import pymysql

# Log to file in production on screen for test
if (config.PROD):
    logging.basicConfig(filename='io.log', level=logging.INFO, format='%(asctime)s %(message)s')
else:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s TEST %(message)s') 

conn = create_db_connection()
c = conn.cursor()

while(True):
    try:
        #get current state
        spot_price = get_spot_price()
        spot_price_avg, spot_price_min, spot_price_max, spot_price_lq, spot_price_uq = get_spot_price_stats()
        import_price = spot_price_lq
        export_price = spot_price_uq
        solar_generation = get_solar_generation()
        power_load = get_existing_load()
        cdp = is_CPD()
        actual_IE = get_actual_IE()
        battery_charge, battery_low, battery_full = get_battery_status()
                  
        # make decision based on current state
        if cdp:
            #there is CPD active so immediately go into low export state
            status = "Exporting - CPD active"
            discharge_to_grid(config.CPD_DISCHARGE_RATE)
     
        elif spot_price<= import_price and not battery_full:
            #import power from grid
            status = "Importing - Spot price low"
            multiplier = (import_price-spot_price)/import_price  
            multiplier = max(0, min(multiplier, 1))
            charge_rate = 1000 * 1.73789 * math.exp(2.85588 * multiplier)
            charge_rate = charge_rate*2.5 #winter multiplier
            charge_from_grid(min(30000, max(1000, int(charge_rate)))) 

        elif spot_price>export_price and not battery_low:
            #export power to grid
            discharge_rate = calc_discharge_rate(spot_price,spot_price_avg)
            discharge_to_grid(discharge_rate)
            status = f"Exporting @ {discharge_rate}- Spot Price High"

        else: 
            #Stop any Importing or Exporting activity  
            reset_to_default() 
            if battery_low:
                status = f"No I/E - Battery Low @ {battery_charge:.1%}"
            elif battery_full:
                status = f"No I/E - Battery Ful @ {battery_charge:.1%}"
            else:
                status = f"No I/E - Battery OK @ {battery_charge:.1%}"
           
    except Exception as e:
        logging.warning("[Error {0}]".format(e))
    
    #log and save record  
    c.execute(f"INSERT INTO DataPoint (SpotPrice, AvgSpotPrice, SolarGeneration , PowerLoad , BatteryCharge , Status, ActualIE) VALUES ({spot_price}, {spot_price_avg}, {solar_generation}, {power_load}, {battery_charge}, '{status}', {actual_IE})")       
    conn.commit()

    sleep(1)