#!/usr/bin/env python3

"""

This code is a control loop for a battery energy storage system.
It makes decisions on whether to import power from the grid to charge the battery,
export power from the battery to the grid, or remain idle based on various system states.

Objectives:
[] Utilize battery cycles to get largest ROI on battery investment
[] Figure out average cost of energy stored - grid v solar and 
    analyse cost + wear and tear v value.

Logic to add:
[] If powers cheep, and expected to get expensive buy a lot.

Info:
CPD - Local lines
Spot price is a National price
130kva line connection at forest lodge

"""

from datetime import time, datetime
import logging
from time import sleep
import config
from powermakerfunctions import (
    adjust_low_price_threshold,
    create_db_connection,
    discharge_to_grid,
    get_spot_price,
    get_spot_price_stats,
    get_solar_generation,
    get_existing_load,
    handle_cpd_event,
    handle_default_case,
    handle_export_to_grid,
    handle_high_power_demand,
    handle_import_from_grid,
    handle_low_spot_price,
    handle_manual_override,
    handle_morning_cpd_period,
    is_CPD,
    get_battery_status,
    get_override,
    get_grid_load,
    is_CPD_period,
    linear_discharge_rate,
    reset_to_default,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=f"%(asctime)s {'PROD' if config.PROD else 'TEST'} %(message)s",
)

def main():
    """Main control loop"""
    conn = create_db_connection()
    cursor = conn.cursor()

    while True:
        try:
            # Get current system state
            status = "unknown"
            spot_price = get_spot_price()
            (
                spot_price_avg,
                spot_price_min,
                spot_price_max,
                import_price,
                export_price,
            ) = get_spot_price_stats()
            solar_generation = get_solar_generation()
            power_load = get_existing_load()
            cdp = is_CPD()

            # Battery info
            battery_charge, battery_low, battery_full = get_battery_status()
            low_price_threshold = adjust_low_price_threshold(battery_charge)

            override, suggested_IE = get_override()
            now = datetime.now().time()
            

            logging.info("%s - battery charging ratio", (100 - battery_charge) / 100)
            logging.info("----------------------")
            logging.info(
                "SPOT PRICE:%s LOW THRESHOLD:%s", spot_price, config.LOW_PRICE_IMPORT
            )

            if override:
                # Manual override
                logging.info(f"Handling manual override\n")
                status = handle_manual_override(status, suggested_IE)
            elif cdp:
                # CPD event active, prioritize selling power
                status = "Exporting - CPD active"
                # discharge_to_grid(config.IE_MIN_RATE*-1)

                # Calculate the export rate based on the battery charge
                export_rate = linear_discharge_rate(battery_charge, config.MIN_BATTERY_FOR_EXPORT, config.IE_MAX_RATE)
                logging.info(f"CPD active - Exporting {export_rate} with status {status} at export rate {export_rate}")
                discharge_to_grid(export_rate)
            elif spot_price <= config.LOW_PRICE_IMPORT and not battery_full:
                # Spot price lower than low price threshold
                logging.info(f"Handling handle_low_spot_price\n")
                status = handle_low_spot_price(status, suggested_IE)
            elif power_load >= config.HIGH_DEMAND_THRESHOLD:
                # High power demand
                logging.info(f"Handling high power demand\n")
                status = handle_high_power_demand(
                    status, spot_price, spot_price_avg, power_load, suggested_IE
                )
            elif spot_price > export_price and spot_price > config.USE_GRID_PRICE and not battery_low:
                # Export power to grid
                logging.info(f"Handling spot_price > export_price and spot_price > config.USE_GRID_PRICE and not battery_low\n")
                status = handle_export_to_grid(status, spot_price, export_price, spot_price_max)
            
            elif spot_price <= import_price and not battery_full:
                # Import power from grid
                logging.info(f"Handling spot_price <= import_price and not battery_full\n")
                status = handle_import_from_grid(
                    status, spot_price, import_price, spot_price_min, power_load
                )
                
            elif spot_price <= low_price_threshold and not battery_full:
                # Spot price lower than low price threshold
                logging.info(f"Handling handle_low_spot_price\n")
                status = handle_low_spot_price(status, suggested_IE)

            elif spot_price <= import_price and not battery_full:
                # Import power from grid
                logging.info(f"Handling spot_price <= import_price and not battery_full\n")
                status = handle_import_from_grid(
                    status, spot_price, import_price, spot_price_min, power_load
                )
            
            # Check with Mike if we need to double check the times for the CPD period
            elif now > time(1, 0) and now < time(6, 30) and battery_charge < 60 and is_CPD_period():
                # Morning CPD period between 1:00 AM and 6:30 AM
                logging.info(f"Handling morning cpd period\n")
                status = handle_morning_cpd_period(
                    status, spot_price, spot_price_avg, suggested_IE, battery_charge
                )
        
            else:
                # Default case
                logging.info(f"Handling default case\n")
                status = handle_default_case(
                    status,
                    battery_charge,
                    battery_low,
                    battery_full,
                    spot_price,
                    spot_price_avg,
                    power_load,
                )

            # Log the current state and decision
            actual_IE = get_grid_load()
            logging.info(f"Status {status}\n")
            cursor.execute(
                f"INSERT INTO DataPoint (SpotPrice, AvgSpotPrice, SolarGeneration, PowerLoad, BatteryCharge, Status, ActualIE, SuggestedIE) VALUES ({spot_price}, {spot_price_avg}, {solar_generation}, {power_load}, {battery_charge}, '{status}', {actual_IE}, {suggested_IE})"
            )
            conn.commit()

        except Exception as e:
            
            """ 
            When exception happens make sure discharge sets to zero
            As we don't know what the price is doing and can get
            stung with high prices
            """
            error = str(e)
            print (error)
            if error == "SpotPriceDataEmpty":
                status = "No Change to Spot Price"
                logging.info(f"Status {status}" )
                c.execute(f"INSERT INTO DataPoint (SpotPrice, AvgSpotPrice, SolarGeneration , PowerLoad , BatteryCharge , Status, ActualIE, SuggestedIE) VALUES (0, 0, 0, 0, 0, '{status}', 0, 0)")
                conn.commit()
                reset_to_default()
                sleep(config.DELAY)
                continue

            elif error == "SpotPriceUnavailable":                
                status = "ERROR Spot Price Unavailable"
                logging.info(f"Status {status}" )
                c.execute(f"INSERT INTO DataPoint (SpotPrice, AvgSpotPrice, SolarGeneration , PowerLoad , BatteryCharge , Status, ActualIE, SuggestedIE) VALUES (0, 0, 0, 0, 0, '{status}', 0, 0)")
                reset_to_default()
                conn.commit()
                continue

            elif error == "DatabaseUnavailable":                
                status = "Database Unavailable"
                logging.info(f"Status {status}" )
                c.execute(f"INSERT INTO DataPoint (SpotPrice, AvgSpotPrice, SolarGeneration , PowerLoad , BatteryCharge , Status, ActualIE, SuggestedIE) VALUES (0, 0, 0, 0, 0, '{status}', 0, 0)")
                conn.commit()
                continue
        
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

        finally:
            conn.commit()
            sleep(config.DELAY)
            continue     

if __name__ == "__main__":
    main()