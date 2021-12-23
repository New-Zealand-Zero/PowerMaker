#!/usr/bin/env python3

# Importing configeration
from datetime import time
import config

# Importing supporting functions
from powermakerfunctions import charging_time, get_battery_charge, is_CPD, get_spot_price, discharge_to_grid, from_solar, existing_load, battery_full, battery_low, charge_from_grid, reset_to_default

# Importing modules
import logging # flexible event logging
import math # mathematical functions
from time import sleep  # To add delay

# Log to file in production on screen for test
if (config.PROD):
    logging.basicConfig(filename='io.log', level=logging.INFO, format='%(asctime)s %(message)s')
else:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s TEST %(message)s') 

time_to_charge=False
chargeing_phase = True
while(True):

    try:
        spot_price=get_spot_price()
        solar_generation = from_solar()
        power_load = existing_load()
        battery_charge = get_battery_charge()

        if is_CPD():
            #there is CPD active so immediately go into low export state
            logging.info(f"CPD: sport price is {get_spot_price()}| battery @ {get_battery_charge()} percent")
            discharge_to_grid(config.CPD_DISCARGE_RATE)
         
        elif spot_price<=config.MAXIMUM_CHARGE_PRICE and not battery_full():
            #import power from grid
            multiplier = (config.MAXIMUM_CHARGE_PRICE-spot_price)/config.MAXIMUM_CHARGE_PRICE
            multiplier = max(0, min(multiplier, 1));
            charge_rate = 1000 * 1.73789 * math.exp(2.85588 * multiplier);
            charge_rate = charge_rate*2.5 #winter multiplier
            # logging.info("CHARGE MULTIPLIER: %s", multiplier)
            charge_from_grid(min(30000, max(1000, int(charge_rate))))

        elif spot_price>config.MINIMUM_DISCHARGE_PRICE and not battery_low() and not charging_time():
            #export power to grid
            multiplier = (spot_price - config.MINIMUM_DISCHARGE_PRICE)/config.MINIMUM_DISCHARGE_PRICE
            multiplier = max(0, min(multiplier, 1));
            discharge_rate = -1000 * 1.73789 * math.exp(2.85588 * multiplier);
            # logging.info("DISCHARGE MULTIPLIER: %s", multiplier)
            discharge_to_grid(max(-30000, min(-1000, int(discharge_rate)))) 

        else:
            if battery_low():
                logging.info("BATTERY LOW: %s precent | discharge paused ", get_battery_charge())
            else:
                logging.info("BATTERY FULL: discharge paused | battery @ %s percent", get_battery_charge())
            reset_to_default()
           
    except Exception as e:
        logging.warning("[Error {0}]".format(e))

    logging.info('\r\n')
    sleep(5)