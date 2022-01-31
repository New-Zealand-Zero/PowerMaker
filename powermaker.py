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
# if (config.PROD):
#     logging.basicConfig(filename='io.log', level=logging.INFO, format='%(asctime)s %(message)s')
# else:
logging.basicConfig(level=logging.INFO, format='%(asctime)s TEST %(message)s') 

conn = create_db_connection()
c = conn.cursor()
while(True):
    try:
        #get current state
        status = "unknown"
        spot_price = get_spot_price()
        spot_price_avg, spot_price_min, spot_price_max, import_price, export_price = get_spot_price_stats()
        solar_generation = get_solar_generation()
        power_load = get_existing_load()
        cdp = is_CPD()
        # actual_IE = get_actual_IE()
        battery_charge, battery_low, battery_full = get_battery_status()
        override, override_rate = get_override()        

        # make decision based on current state
        if (override):
            #Manual override
            if (override_rate<0):
                status = f"Exporting - Manual Override"
                discharge_to_grid(override_rate)
            elif (override_rate>0):
                status = f"Importing - Manual Override"
                charge_from_grid(override_rate)
            else:
                status = f"No I/E - Manual Override"
                reset_to_default() 
        elif spot_price>export_price and not battery_low:
            #export power to grid
            status = f"Exporting - Spot Price High"
            rate = calc_discharge_rate(spot_price,export_price,spot_price_max)
            discharge_to_grid(rate)
        elif cdp:
            #there is CPD active so immediately go into low export state
            status = "Exporting - CPD active"
        elif spot_price<= import_price and not battery_full:
            #import power from grid
            status = "Importing - Spot price low"
            rate = calc_discharge_rate(spot_price,import_price,spot_price_min)
            charge_from_grid(rate)
        else: 
            #Stop any Importing or Exporting activity  
            reset_to_default() 
            if battery_low:
                status = f"No I/E - Battery Low @ {battery_charge} %"
            elif battery_full:
                status = f"No I/E - Battery Ful @ {battery_charge} %"
            else:
                status = f"No I/E - Battery OK @ {battery_charge} %"
           
    except Exception as e:
        logging.warning("[Error {0}]".format(e))
    
    #log and save record
    sleep(1)
    actual_IE = get_existing_load()
    grid_load = get_grid_load()
    logging.info(f"Status {status} \n" )

    c.execute(f"INSERT INTO DataPoint (SpotPrice, AvgSpotPrice, SolarGeneration , PowerLoad , BatteryCharge , Status, ActualIE) VALUES ({spot_price}, {spot_price_avg}, {solar_generation}, {power_load}, {battery_charge}, '{status}', {actual_IE})")       
    conn.commit()

    sleep(config.DELAY)
