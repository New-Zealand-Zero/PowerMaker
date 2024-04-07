#!/usr/bin/env python3

"""
This code is a control loop for a battery energy storage system.
It makes decisions on whether to import power from the grid to charge the battery,
export power from the battery to the grid, or remain idle based on various system states.
"""

from datetime import time, datetime
import logging
import math
from time import sleep
import config
from powermakerfunctions import (
    create_db_connection,
    get_spot_price,
    get_spot_price_stats,
    get_solar_generation,
    get_existing_load,
    handle_cpd_event,
    handle_default_case,
    handle_exception,
    handle_export_to_grid,
    handle_high_power_demand,
    handle_import_from_grid,
    handle_low_spot_price,
    handle_manual_override,
    handle_morning_cpd_period,
    is_CPD,
    get_battery_status,
    get_override,
    calc_discharge_rate,
    calc_charge_rate,
    discharge_to_grid,
    charge_from_grid,
    reset_to_default,
    get_grid_load,
    is_CPD_period,
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
            battery_charge, battery_low, battery_full = get_battery_status()
            override, suggested_IE = get_override()
            now = datetime.now().time()

            logging.info("%s - battery charging ratio", (100 - battery_charge) / 100)
            logging.info("----------------------")
            logging.info(
                "SPOT PRICE:%s LOW THRESHOLD:%s", spot_price, config.LOW_PRICE_IMPORT
            )

            # Make decision based on current state
            if override:
                # Manual override
                handle_manual_override(status, suggested_IE)
            elif cdp:
                # CPD event active, prioritize selling power
                handle_cpd_event(status, battery_charge)
            elif spot_price <= config.LOW_PRICE_IMPORT and not battery_full:
                # Spot price lower than low price threshold
                handle_low_spot_price(status, suggested_IE)
            elif power_load >= config.HIGH_DEMAND_THRESHOLD:
                # High power demand
                handle_high_power_demand(
                    status, spot_price, spot_price_avg, power_load, suggested_IE
                )
            elif (
                spot_price > export_price
                and spot_price > config.USE_GRID_PRICE
                and not battery_low
            ):
                # Export power to grid
                handle_export_to_grid(status, spot_price, export_price, spot_price_max)
            elif spot_price <= import_price and not battery_full:
                # Import power from grid
                handle_import_from_grid(
                    status, spot_price, import_price, spot_price_min, power_load
                )
            elif (
                now > time(1, 0)
                and now < time(6, 30)
                and battery_charge < 60
                and is_CPD_period()
            ):
                # Morning CPD period
                handle_morning_cpd_period(
                    status, spot_price, spot_price_avg, suggested_IE
                )
            else:
                # Default case
                handle_default_case(
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
            handle_exception(e, cursor, conn)

        finally:
            conn.commit()
            sleep(config.DELAY)

""" Helper Functions, can be moved to a separate file """

# def handle_manual_override(status, suggested_IE):
#     """Handle manual override"""
#     if suggested_IE < 0:
#         status = "Exporting - Manual Override"
#         discharge_to_grid(suggested_IE)
#     elif suggested_IE > 0:
#         status = "Importing - Manual Override"
#         charge_from_grid(suggested_IE)
#     else:
#         status = "No I/E - Manual Override"
#         reset_to_default()


# def handle_cpd_event(status, battery_charge):
#     """Handle CPD event, prioritize selling power"""
#     export_rate = math.log2(battery_charge + 1)  # Calculate log base 2 of battery_charge
#     status = "Exporting - CPD active"
#     discharge_to_grid(export_rate)


# def handle_low_spot_price(status, suggested_IE):
#     """Handle low spot price"""
#     status = "Importing - Spot price < min"
#     suggested_IE = config.IE_MAX_RATE
#     charge_from_grid(suggested_IE)


# def handle_high_power_demand(status, spot_price, spot_price_avg, power_load, suggested_IE):
#     """Handle high power demand"""
#     if spot_price <= config.USE_GRID_PRICE:
#         status = "Price lower than battery cycle cost"
#         logging.info("SPOT PRICE low and demand high")
#         suggested_IE = config.IE_MAX_RATE
#         charge_from_grid(suggested_IE)
#     elif spot_price < spot_price_avg:
#         status = f"Price lower than average: {power_load}"
#         charge_from_grid(power_load)
#     else:
#         status = "Price high run on batteries"
#         reset_to_default()


# def handle_export_to_grid(status, spot_price, export_price, spot_price_max):
#     """Handle exporting power to grid"""
#     status = "Exporting - Spot Price High"
#     suggested_IE = calc_discharge_rate(spot_price, export_price, spot_price_max)
#     discharge_to_grid(suggested_IE)


# def handle_import_from_grid(status, spot_price, import_price, spot_price_min, power_load):
#     """Handle importing power from grid"""
#     status = "Importing - Spot price low"
#     suggested_IE = calc_charge_rate(spot_price, import_price, spot_price_min) + power_load
#     charge_from_grid(suggested_IE)


# def handle_morning_cpd_period(status, spot_price, spot_price_avg, suggested_IE):
#     """Handle morning CPD period"""
#     logging.info("CPD CHARGING PERIOD")
#     if spot_price <= spot_price_avg:
#         logging.info("SPOT PRICE IS LESS THAN AVERAGE CHARGING")
#         suggested_IE = config.IE_MAX_RATE * (100 - battery_charge) / 100
#         status = f"CPD Night Charge: {suggested_IE}"
#         charge_from_grid(suggested_IE)
#     else:
#         logging.info("SPOT PRICE IS MORE AVERAGE PAUSE")
#         status = "CPD Night Charge: Price High"


# def handle_default_case(
#     status, battery_charge, battery_low, battery_full, spot_price, spot_price_avg, power_load
# ):
#     """Handle default case"""
#     if is_CPD_period() and spot_price <= spot_price_avg * 1:
#         suggested_IE = power_load
#         status = "CPD: covering"
#         if battery_charge > 50:
#             status = "CPD: partial covering"
#             suggested_IE = suggested_IE * ((100 - battery_charge) / 100)  # Take the inverse of the battery from the grid if battery is more than half full
#         charge_from_grid(suggested_IE)

#     else:
#         reset_to_default()
#         if battery_low:
#             status = f"No I/E - Battery Low @ {battery_charge} %"
#         elif battery_full:
#             status = f"No I/E - Battery Full @ {battery_charge} %"
#         else:
#             status = f"No I/E - Battery OK @ {battery_charge} %"