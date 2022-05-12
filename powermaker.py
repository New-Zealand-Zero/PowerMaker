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

# Logging
logging.basicConfig(level=logging.INFO, format=f'%(asctime)s {"PROD" if config.PROD else "TEST"} %(message)s') 

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
        battery_charge, battery_low, battery_full = get_battery_status()
        override, suggested_IE = get_override()     
        now = datetime.now().time()

        logging.info("%s %s %s %s" %(battery_charge < 80 , is_CPD_period(), now > time(1,0) , now < time(6,30)))

        # make decision based on current state
        if (override):
            #Manual override
            if (suggested_IE<0):
                status = f"Exporting - Manual Override"
                discharge_to_grid(suggested_IE)
            elif (suggested_IE>0):
                status = f"Importing - Manual Override"
                charge_from_grid(suggested_IE)
            else:
                status = f"No I/E - Manual Override"
                reset_to_default() 
        elif cdp:
            #there is CPD active so immediately go into low export state
            status = "Exporting - CPD active"
            discharge_to_grid(config.IE_MIN_RATE*-1)
    

        elif spot_price<= config.LOW_PRICE_IMPORT and not battery_full:
            #spot price less than Low price min import
            status = "Importing - Spot price < min"
            suggested_IE = config.IE_MAX_RATE
            charge_from_grid(suggested_IE)
        elif spot_price>export_price and not battery_low:
            #export power to grid if price is greater than calc export price
            status = f"Exporting - Spot Price High"
            suggested_IE = calc_discharge_rate(spot_price,export_price,spot_price_max)
            discharge_to_grid(suggested_IE)
        elif spot_price<= import_price and not battery_full:
            #import power from grid if price is less than calc export price
            status = "Importing - Spot price low"
            suggested_IE = calc_charge_rate(spot_price,import_price,spot_price_min)
            charge_from_grid(suggested_IE+power_load) # move to cover existing power consumption plus import 


        #winter cpd dodging - charge up to 80% if spot price is <= spot price average
        elif now > time(1,0) and now < time(6,30) and battery_charge < 80 and is_CPD_period():
            logging.info("CPD CHARGING PERIOD")
            if spot_price <= spot_price_avg*1.1:
                logging.info("SPOT PRICE IS LESS THAN AVERAGE CHARGING")
                status="Importing - Winter Night Charging"
                charge_from_grid(config.IE_MAX_RATE)
            else:
                logging.info("SPOT PRICE IS MORE AVERAGE PAUSE")
                status="No I/# - Winter Night Charging spot price high"


        else: 
            #Stop any Importing or Exporting activity  
            if is_CPD_period() and spot_price <= spot_price_avg:
                charge_from_grid(power_load) # if its the cpd period then run power load at average price when available to make sure batteries are not depleted for night time cpd periods
                status = f"CPD Period: Gridpoint set to consumption @ {power_load} %"
            else:
                reset_to_default() 
                if battery_low:
                    status = f"No I/E - Battery Low @ {battery_charge} %"
                elif battery_full:
                    status = f"No I/E - Battery Ful @ {battery_charge} %"
                else:
                    status = f"No I/E - Battery OK @ {battery_charge} %"
        
        actual_IE = get_grid_load()
        c.execute(f"INSERT INTO DataPoint (SpotPrice, AvgSpotPrice, SolarGeneration , PowerLoad , BatteryCharge , Status, ActualIE, SuggestedIE) VALUES ({spot_price}, {spot_price_avg}, {solar_generation}, {power_load}, {battery_charge}, '{status}', {actual_IE}, {suggested_IE})")       
        #log and save record
        logging.info(f"Status {status} \n" )
        conn.commit()

    except Exception as e:
        error = str(e)
        print (error)
        if error == "SpotPriceUnavailable":                
            status = "ERROR Spot Price Unavailable"
            logging.info(f"Status {status}" )
            c.execute(f"INSERT INTO DataPoint (SpotPrice, AvgSpotPrice, SolarGeneration , PowerLoad , BatteryCharge , Status, ActualIE, SuggestedIE) VALUES (0, 0, 0, 0, 0, '{status}', 0, 0)")
            conn.commit()
        elif error == "DatabaseUnavailable":                
            status = "Database Unavailable"
            logging.info(f"Status {status}" )
            c.execute(f"INSERT INTO DataPoint (SpotPrice, AvgSpotPrice, SolarGeneration , PowerLoad , BatteryCharge , Status, ActualIE, SuggestedIE) VALUES (0, 0, 0, 0, 0, '{status}', 0, 0)")
            conn.commit()
       
        #try and stop all I/E as an exception has occurred
        try:
            reset_to_default()
            status = "ERROR occurred I/E has been stopped"
        except Exception as e:
            error = str(e)
            status = f"ERROR unable to stop I/E: {error}"

        logging.info(f"Status {status} \n" )
        c.execute(f"INSERT INTO DataPoint (SpotPrice, AvgSpotPrice, SolarGeneration , PowerLoad , BatteryCharge , Status, ActualIE, SuggestedIE) VALUES (0, 0, 0, 0, 0, '{status}', 0, 0)")
        conn.commit()
    
    sleep(config.DELAY)
