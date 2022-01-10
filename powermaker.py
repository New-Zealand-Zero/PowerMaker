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

# time_to_charge=False   ??? Do we need this
# chargeing_phase = True  ??? Do we need this
while(True):

    try:
        #get current state
        spot_price = get_spot_price()
        avg_spot_price = get_avg_spot_price()
        export_price = avg_spot_price + (0.5 * config.SPOT_PRICE_IE_SPREAD)
        import_price = avg_spot_price - (0.5 * config.SPOT_PRICE_IE_SPREAD)
        solar_generation = get_solar_generation()
        power_load = get_existing_load()
        battery_charge = get_battery_charge()
        battery_full = get_battery_full()
        battery_low = get_battery_low()
        cdp = is_CPD()
                  
        # make decision based on current state
        if cdp:
            #there is CPD active so immediately go into low export state
            status = "Exporting - CPD active"
            discharge_to_grid(config.CPD_DISCHARGE_RATE) # ??should we make the min?
     
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
            status = "Exporting - Spot Price High"
            multiplier = (spot_price - export_price)/export_price
            discharge_rate = -1000 * 1.73789 * math.exp(2.85588 * multiplier)
            multiplier = max(0, min(multiplier, 1))
            discharge_rate = -1000 * 1.73789 * math.exp(2.85588 * multiplier)
            discharge_to_grid(max(-30000, min(-1000, int(discharge_rate))))

        else: 
            #Stop any Importing or Exporting activity  
            reset_to_default() 
            if battery_low:
                status = f"No I/E - Battery Low @ {battery_charge} percent"
            elif battery_full:
                status = "No I/E - Battery Full"
            else:
                status = "No I/E - Battery OK @ {battery_charge} percent"
           
    except Exception as e:
        logging.warning("[Error {0}]".format(e))
    
    #log and save record  
    logging.info(f"Status {status} \n")
    c.execute(f"INSERT INTO DataPoint (SpotPrice, AvgSpotPrice, SolarGeneration , PowerLoad , BatteryCharge , Status) VALUES ({spot_price}, {avg_spot_price}, {solar_generation}, {power_load}, {battery_charge}, '{status}')")       
    conn.commit()

    sleep(5)