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

        logging.info("%s - battery charging ratio" %((100-battery_charge)/100))
        logging.info("----------------------")
        logging.info("SPOT PRICE:%s LOW THREHOLD:%s" %(spot_price,config.LOW_PRICE_IMPORT))

        # make decision based on current state
        if (config.OVERRIDE_IE):
            discharge_to_grid(config.OVERRIDE_RATE)
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
            # discharge_to_grid(config.IE_MIN_RATE*-1)

            # Calculate the export rate based on the battery charge
            # Starting off with a linear discharge rate, but this could be changed to a more complex function
            # But want to test that we can have discharge change from 100 battery to the config
            # for MIN_BATTERY_FOR_EXPORT. 
            suggested_IE = linear_discharge_rate(battery_charge, config.MIN_BATTERY_FOR_EXPORT, config.CPD_MIN_BATTERY_EXPORT_RATE, config.IE_MAX_RATE)
            logging.info(f"CPD active - Exporting {suggested_IE} with status {status} - Target min battery {config.MIN_BATTERY_FOR_EXPORT}, current battery {battery_charge}")
            discharge_to_grid(suggested_IE)

        elif spot_price<= config.LOW_PRICE_IMPORT and not battery_full:
            #spot price less than Low price min import
            status = "Importing - Spot price < min"
            suggested_IE = config.IE_MAX_RATE
            charge_from_grid(suggested_IE)

        #High power use - conditions added to handle business case for substantial power consumption
        elif power_load >= config.HIGH_DEMAND_THRESHOLD:
            if spot_price <= config.USE_GRID_PRICE:
                status = f"Price lower than battery cycle cost"
                logging.info("SPOT PRICE low and demand high")
                suggested_IE = config.IE_MAX_RATE
                charge_from_grid(suggested_IE) #run all consumption from grid and keep batteries charged
            elif spot_price < spot_price_avg:
                status = f"Price lower than average: {power_load}"
                charge_from_grid(power_load) #just cover power load
            else:
                status = f"Price high run on batteries"
                reset_to_default() # move to 100% battery power as price is too  high

        elif spot_price>export_price and spot_price > config.USE_GRID_PRICE and not battery_low:
            #export power to grid if price is greater than calc export price
            status = f"Exporting - Spot Price High"
            suggested_IE = calc_discharge_rate(spot_price,export_price,spot_price_max)
            discharge_to_grid(suggested_IE)
        elif spot_price<= import_price and not battery_full:
            #import power from grid if price is less than calc export price
            status = "Importing - Spot price low"
            suggested_IE = calc_charge_rate(spot_price,import_price,spot_price_min)+power_load # move to cover existing power consumption plus import 
            charge_from_grid(suggested_IE) 

        #winter cpd dodging - charge up to 80% if spot price is <= spot price average
        elif now > time(1,0) and now < time(6,30) and battery_charge < 60 and is_CPD_period():
            logging.info("CPD CHARGING PERIOD")
            if spot_price <= spot_price_avg: #take up to 20% higher price than average to make sure these batteries have enough to cover morning cpd
                logging.info("SPOT PRICE IS LESS THAN AVERAGE CHARGING")
                suggested_IE = config.IE_MAX_RATE * (100-battery_charge)/100 #slow down as battery gets more full
                status = f"CPD Night Charge: {suggested_IE}"
                charge_from_grid(suggested_IE)
            else:
                logging.info("SPOT PRICE IS MORE AVERAGE PAUSE")
                status="CPD Night Charge: Price High"

        else:   
            if is_CPD_period() and spot_price <= spot_price_avg*1:
                suggested_IE = power_load
                status = f"CPD: covering" 
                if battery_charge > 50:
                    status = f"CPD: partial covering" 
                    suggested_IE = suggested_IE * ((100-battery_charge)/100) #take the inverse of the battery from the grid if battery more than half full
                charge_from_grid(suggested_IE)
                

            else:
                reset_to_default() 
                if battery_low:
                    status = f"No I/E - Battery Low @ {battery_charge} %"
                elif battery_full:
                    status = f"No I/E - Battery Ful @ {battery_charge} %"
                else:
                    status = f"No I/E - Battery OK @ {battery_charge} %"
        
        actual_IE = get_grid_load()
        logging.info(f"Status {status} \n" )
        c.execute(f"INSERT INTO DataPoint (SpotPrice, AvgSpotPrice, SolarGeneration , PowerLoad , BatteryCharge , Status, ActualIE, SuggestedIE) VALUES ({spot_price}, {spot_price_avg}, {solar_generation}, {power_load}, {battery_charge}, '{status}', {actual_IE}, {suggested_IE})")       

        conn.commit()

    except Exception as e:
        # When exeption happens make sure discharge sets to zero
        # As we don't know what the price is doing and can get stung with high prices
        # Prices
        error = str(e)
        print (error)
        if error == "SpotPriceDataEmpty":
            status = "No Change to Spot Price"
            logging.info(f"Status {status}" )
            c.execute(f"INSERT INTO DataPoint (SpotPrice, AvgSpotPrice, SolarGeneration , PowerLoad , BatteryCharge , Status, ActualIE, SuggestedIE) VALUES (0, 0, 0, 0, 0, '{status}', 0, 0)")
            conn.commit()
            sleep(config.DELAY)
            continue

        elif error == "SpotPriceUnavailable":                
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
            status = f"ERROR unable to stop I/E"

        logging.info(f"Status {status} \n" )
        c.execute(f"INSERT INTO DataPoint (SpotPrice, AvgSpotPrice, SolarGeneration , PowerLoad , BatteryCharge , Status, ActualIE, SuggestedIE) VALUES (0, 0, 0, 0, 0, '{status}', 0, 0)")
        conn.commit()
    
    sleep(config.DELAY)

