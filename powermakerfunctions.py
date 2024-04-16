#!/usr/bin/env python3

# Importing configuration
import math
from re import S
import config

# Importing modules
from datetime import datetime, time, timedelta # obtain and format dates and time
import urllib.request, urllib.parse, urllib.error # extensible library for opening URLs
import http.client # classes which implement the client side of the HTTP and HTTPS protocols
import json # JSON encoder and decoder
import logging # flexible event logging
import random  # generate random number for testing
from pymodbus.constants import Defaults
from pymodbus.constants import Endian
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder, Endian, BinaryPayloadDecoder
import numpy as np
import matplotlib.pyplot as plt
import pymysql
import requests
import traceback

# Logging
logging.basicConfig(level=logging.INFO, format=f'%(asctime)s {"PROD" if config.PROD else "TEST"} %(message)s') 

if (config.PROD):
    client = ModbusClient('192.168.86.34', port='502', auto_open=True, auto_close=True)

""" 
SPOT PRICE FUNCTIONS
"""
def get_spot_price():
    """return the latest power spot price from OCP
     Keyword arguments: None
    """
    # try:
    #     spot_price =0
    #     if (config.PROD):
    #         now = datetime.now().strftime("%Y-%m-%dT%H:%M")
    #         Defaults.Timeout = 25
    #         Defaults.Retries = 5
    #         params = urllib.parse.urlencode({
    #                 '$filter': 'PointOfConnectionCode eq \'CML0331\'',
    #                 '&filter': 'TradingDate eq datetime'+now+''
    #         })
    #         request_headers = {
    #         'Ocp-Apim-Subscription-Key': config.OCP_APIM_SUBSCRIPTION_KEY
    #         }
    #         conn = http.client.HTTPSConnection('emi.azure-api.net')
    #         conn.request("GET", "/real-time-prices/?%s" % params, "{body}", request_headers)
    #         response = conn.getresponse()
    #         data = response.read()
            
    #     else:
    #         #generate test data
    #         conn = create_db_connection()       
    #         c = conn.cursor()
    #         c.execute("SELECT SpotPrice from DataPoint where RecordID = (SELECT Max(RecordID) from DataPoint)")
    #         row = c.fetchone()
    #         c.close()
    #         conn.close()
    
    #         spot_price = row[0] + float("{0:.5f}".format(random.uniform(-0.10001, 0.10001)))
    #         if spot_price < 0:
    #             spot_price *= -1     

    try:
        spot_price=0
        if (config.PROD):
            

            r = requests.post('https://api.electricityinfo.co.nz/login/oauth2/token', json={
                "grant_type": "client_credentials",
                "client_id": config.WITS_CLIENT_ID,
                "client_secret": config.WITS_CLIENT_SECRET
            })

            access_token= r.json().get('access_token')

            print (access_token)

            conn = http.client.HTTPSConnection("api.electricityinfo.co.nz")
            headers = { 'accept': "application/json", 'Authorization':'Bearer %s' %access_token }

            # conn.request("GET", "/api/market-prices/v1/schedules", headers=headers)

            # res = conn.getresponse()
            # data = res.read()

            # print(data.decode("utf-8"),"\n")

            # conn.request("GET", "", headers=headers)

            # res = conn.getresponse()
            # data = res.read()

            # print(data.decode("utf-8"),"\n")

            # # conn.request("GET", "/api/market-prices/v1/prices?schedules=RTP&marketType=R&nodes=%CML0331&from=&to=&back=&forward=&offset=", headers=headers)

            # # res = conn.getresponse()
            # # data = res.read()

            # # print("this is the one \n",data.decode("utf-8"),"\n")

            now = datetime.now() - timedelta(minutes=1)
            now = now.strftime("%Y-%m-%dT%H:%M:%S")

            # print("/api/market-prices/v1/schedules/RTP/prices?offset=0&nodes=%s&marketType=E&from=%s" %(config.PRICE_NODE,now))
            # conn.request("GET", "/api/market-prices/v1/schedules/RTP/prices?offset=0&nodes=%s&marketType=E&from=%s" %(config.PRICE_NODE,now), headers=headers)

            conn.request("GET", "/api/market-prices/v1/schedules/RTD/prices?marketType=E&nodes=%s" %(config.PRICE_NODE), headers=headers)

            res = conn.getresponse()
            data = res.read()

            json_data = json.loads(data.decode('utf-8'))
            spot_price = json_data['prices'][0]['price']/1000

        else:
            #generate test data
            conn = create_db_connection()       
            c = conn.cursor()
            c.execute("SELECT SpotPrice from DataPoint where RecordID = (SELECT Max(RecordID) from DataPoint)")
            row = c.fetchone()
            c.close()
            conn.close()
    
            spot_price = row[0] + float("{0:.5f}".format(random.uniform(-0.10001, 0.10001)))
            if spot_price < 0:
                spot_price *= -1     

        logging.info(f"Spot price ${spot_price}")
        return spot_price

    except Exception as e:
        traceback.print_exc()
        raise NameError('SpotPriceUnavailable')  

def get_spot_price_stats():
    """return average spot price data
    Keyword arguments: None
    """  
    conn = create_db_connection()
    c = conn.cursor()
    c.execute("SELECT SpotPrice from DataPoint where Timestamp > now() - interval 5 day AND SpotPrice and LEFT(status,5) <> 'ERROR'")
    result = c.fetchall()
    c.close()
    conn.close()

    if (result):
        spot_prices = []
        x=0
        for i in result:
            x += 1
            spot_prices.append(i[0])

        spot_price_avg=np.average(spot_prices)
        spot_price_min=np.min(spot_prices)
        spot_price_max=np.max(spot_prices)
        import_price=np.quantile(spot_prices,config.IMPORT_QUANTILE)
        export_price=np.quantile(spot_prices,config.EXPORT_QUANTILE)+.1
    else:
        spot_price_avg=0
        spot_price_min=0
        spot_price_max=0
        import_price=0
        export_price=0
    
    #New theory here is to always import if cheap enough but only export if MIN Margin is high enough
    # update the import price if less than min margin
    # if (import_price > (spot_price_avg - config.HALF_MIN_MARGIN)):
    #     logging.info (f"calculated import price {import_price:.4f} below min margin updated to min")
    #     import_price = spot_price_avg - config.HALF_MIN_MARGIN
    
    # update the export price if less than if less than min margin
    if (export_price < (spot_price_avg + config.MIN_MARGIN)):
        logging.info (f"calculated export price {export_price:.4f} below min margin updated to min")
        export_price = spot_price_avg + config.MIN_MARGIN
    
    logging.info(f"Average Spot Price {spot_price_avg:.4f} spot_price_min:{spot_price_min:.4f} spot_price_max: {spot_price_max:.4f} import_price:{import_price:.4f} export_price:{export_price:.4f}")
    return spot_price_avg, spot_price_min, spot_price_max, import_price, export_price

def handle_low_spot_price(status, suggested_IE):
    """Handle low spot price"""
    status = "Importing - Spot price < min"
    suggested_IE = config.IE_MAX_RATE
    charge_from_grid(suggested_IE)
    return status

"""
CONTROL PERIOD STATUS FUNCTIONS
"""

def is_CPD():
    """check if CONTROL PERIOD STATUS is active - a period of peak loading on distribution network.
    Keyword arguments: None
    """

    if (config.PROD):
        result = client.read_holding_registers(3422, unit=1)
        result = client.read_holding_registers(3422, unit=1)
        logging.info("CPD ACTIVE" if result.registers[0] == 3 else "CPD INACTIVE")
        return result.registers[0] == 3
    else:
        if (random.randint(1, 10) > 8):
            logging.info("CPD ACTIVE")
            return True
        else:
            logging.info("CPD INACTIVE")
            return False

def handle_cpd_event(status, battery_charge):
    """Handle CPD event, prioritize selling power"""
    export_rate = math.log2(battery_charge + 1)  # Calculate log base 2 of battery_charge
    status = "Exporting - CPD active"
    logging.info(f"CPD active - Exporting {export_rate} with status {status}")
    discharge_to_grid(export_rate)
    return status

def is_CPD_period():
    #Auora congestion period runs from roughly mid may to mid september
    month = datetime.now().month
    return month in [5,6,7,8,9]

def handle_morning_cpd_period(status, spot_price, spot_price_avg, suggested_IE, battery_charge):
    """Handle morning CPD period"""
    logging.info("CPD CHARGING PERIOD")
    if spot_price <= spot_price_avg:
        logging.info("SPOT PRICE IS LESS THAN AVERAGE CHARGING")
        suggested_IE = config.IE_MAX_RATE * (100 - battery_charge) / 100
        status = f"CPD Night Charge: {suggested_IE}"
        charge_from_grid(suggested_IE)
    else:
        logging.info("SPOT PRICE IS MORE AVERAGE PAUSE")
        status = "CPD Night Charge: Price High"
    return status

"""
GRID FUNCTIONS
"""

def charge_from_grid(rate_to_charge):
    """ import power from grid
    Keyword arguments: rate to charge
    """

    if (config.PROD):
        client.write_register(2703, int(rate_to_charge*0.01 if rate_to_charge > 0 else 1000))

    logging.info(f"Importing from Grid @ {rate_to_charge/1000} kWh" )
    return

def discharge_to_grid(rate_to_discharge):
    """ export power to grid
    Keyword arguments: rate to discharge    
    """

    logging.info(f"Suggested export to Grid @ {rate_to_discharge/1000} kWh" )
    if (config.PROD):
        rate_to_discharge=int(rate_to_discharge*0.01)
        builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Big)
        builder.reset()
        builder.add_16bit_int(rate_to_discharge if rate_to_discharge < 0 else -1000)
        payload = builder.to_registers()
        client.write_register(2703, payload[0])  
    
    return

def get_grid_load():
    if (config.PROD):
        l1 = client.read_holding_registers(820).registers[0]
        l2 = client.read_holding_registers(821).registers[0]
        l3 = client.read_holding_registers(822).registers[0]
        grid_load= l1 + l2 + l3
    else:
        grid_load = random.randint(-20000, 20000)
    logging.info(f"Grid Load {grid_load}")
    return grid_load

def handle_export_to_grid(status, spot_price, export_price, spot_price_max):
    """Handle exporting power to grid"""
    status = "Exporting - Spot Price High"
    suggested_IE = calc_discharge_rate(spot_price, export_price, spot_price_max)
    discharge_to_grid(suggested_IE)
    return status

def handle_import_from_grid(status, spot_price, import_price, spot_price_min, power_load):
    """Handle importing power from grid"""
    status = "Importing - Spot price low"
    suggested_IE = calc_charge_rate(spot_price, import_price, spot_price_min) + power_load
    charge_from_grid(suggested_IE)
    return status

""" 
SOLAR FUNCTIONS
"""

def get_solar_generation():
    """return current solar generation
    Keyword arguments: None
    """
    if (config.PROD):
        solar_generation = client.read_holding_registers(808).registers[0]
        solar_generation += client.read_holding_registers(809).registers[0]
        solar_generation += client.read_holding_registers(810).registers[0]
    else:
        solar_generation = random.randint(0, 20000)

    logging.info(f"Solar Generation {solar_generation}")
    return solar_generation 

"""
OVERRIDE FUNCTIONS
"""

def get_override():
    """return if manual override state
    Keyword arguments: None
    """      
    conn = create_db_connection()
    c = conn.cursor()
    c.execute("SELECT ConfigValue from Config where ConfigID = 'Override'")
    row = c.fetchone()
    c.close()
    conn.close()

    if (row[0] == "N"):
        logging.info(f"No manual override")
        return False, 0
    else:
        logging.info(f"Manual override")
        return True, int(row[0])

def update_override(override, rate):
    conn = create_db_connection()
    c = conn.cursor()
    if (override):
        c.execute(f"UPDATE Config SET ConfigValue = {rate} where ConfigID = 'Override'")
    else:
        c.execute(f"UPDATE Config SET ConfigValue = 'N' where ConfigID = 'Override'")
    conn.commit()
    c.close()
    conn.close()

def handle_manual_override(status, suggested_IE):
    """Handle manual override"""
    if suggested_IE < 0:
        status = "Exporting - Manual Override"
        discharge_to_grid(suggested_IE)
    elif suggested_IE > 0:
        status = "Importing - Manual Override"
        charge_from_grid(suggested_IE)
    else:
        status = "No I/E - Manual Override"
        reset_to_default()
    return status

""" 
DEFAULT FUNCTIONS
"""
    
def get_battery_status():
    """
    return the battery charge and status
    Keyword arguments: None
    """
    if (config.PROD):  
        result = client.read_holding_registers(843)
        battery_charge= int(result.registers[0])
    else:
        battery_charge=  random.randint(0, 100)    
    
    battery_low = battery_charge <= config.LOW_BATTERY_THRESHOLD
    battery_full = battery_charge >= config.CHARGED_BATTERY_THRESHOLD

    logging.info(f"Battery: {battery_charge}% Battery_low: {battery_low} Battery_full: {battery_full}" )
    return battery_charge, battery_low, battery_full

def reset_to_default():

    if (config.PROD):
        client.write_register(2703,int(0))

def get_existing_load():
    """return current power load
    Keyword arguments: None
    """    
    if (config.PROD):    
        l1 = client.read_holding_registers(817).registers[0]
        l2 = client.read_holding_registers(818).registers[0]
        l3 = client.read_holding_registers(819).registers[0]
        power_load = l1 + l2 + l3
    else:
        power_load= random.randint(5000, 10000)

    logging.info(f"Power Load {power_load}")
    return power_load
    
def get_actual_IE():
    """return current power load
    Keyword arguments: None
    """    

    if (not config.PROD):    
        power_load = client.read_holding_registers(2600).registers[0]
        power_load += client.read_holding_registers(2601).registers[0]
        power_load += client.read_holding_registers(2602).registers[0]
    else:
        power_load= random.randint(-config.IE_MAX_RATE, config.IE_MAX_RATE)

    logging.info(f"Actual IE {power_load}")
    return power_load

def get_status():
    """return current status
    Keyword arguments: None
    """      
    conn = create_db_connection()
    c = conn.cursor()
    c.execute("SELECT * from DataPoint where RecordID = (SELECT Max(RecordID) from DataPoint)")
    row = c.fetchone()
    c.close()
    conn.close()

    return row

def get_consumption():
    if (config.PROD):
        l1 = client.read_holding_registers(817).registers[0]
        l2 = client.read_holding_registers(818).registers[0]
        l3 = client.read_holding_registers(819).registers[0]
        consumption = l1 + l2 + l3
    else:
        consumption = random.randint(0, 20000)
    logging.info(f"Consumption {consumption}")
    return consumption

def calc_discharge_rate(spot_price,export_price,spot_price_max):

    #linear scale spot price to exp input value
    scaled_price= np.interp(spot_price, [export_price , spot_price_max],[config.EXP_INPUT_MIN , config.EXP_INPUT_MAX ])

    #Apply the exp function to exp_value less the min
    scaled_margin_exp = np.exp(scaled_price) - np.exp(config.EXP_INPUT_MIN)

    #Calc the value to scale the max exp value to the max discharge rate
    multiplier = (config.IE_MAX_RATE-config.IE_MIN_RATE)/np.exp(config.EXP_INPUT_MAX) 

    #linear scale the exp function applied value to discharge rate 
    discharge_rate = - int(config.IE_MIN_RATE + (scaled_margin_exp*multiplier))
    return discharge_rate

def calc_charge_rate(spot_price,import_price,spot_price_min):

    #linear scale spot price to exp input value
    scaled_price= np.interp(spot_price, [spot_price_min , import_price , ],[config.EXP_INPUT_MAX, config.EXP_INPUT_MIN  ])

    #Apply the exp function to exp_value less the min
    scaled_margin_exp = np.exp(scaled_price) - np.exp(config.EXP_INPUT_MIN)

    #Calc the value to scale the max exp value to the max discharge rate
    multiplier = (config.IE_MAX_RATE-config.IE_MIN_RATE)/np.exp(config.EXP_INPUT_MAX) 

    #linear scale the exp function applied value to discharge rate 
    discharge_rate = int(config.IE_MIN_RATE + (scaled_margin_exp*multiplier))

    return discharge_rate

def update_graphs():

    conn = create_db_connection()
    c = conn.cursor()
    c.execute("SELECT spotprice, actualIE from DataPoint where timestamp >= DATE_SUB(NOW(),INTERVAL 1 DAY) and LEFT(status,5) <> 'ERROR'")
    result = c.fetchall()
    c.close()  

    points = []
    spot_prices = []
    actual_import = []
    actual_export = []
    
    x=0
    for i in result:
        x += 1
        points.append(x)
        spot_prices.append(i[0])
        if (i[1] > 0 ):
            actual_import.append(i[1])
        else:
            actual_import.append(0)

        if (i[1] < 0 ):
            actual_export.append(abs(i[1]))
        else:
            actual_export.append(0)

    plt.plot(points, spot_prices)
    plt.xlabel('Record')
    plt.ylabel('Spot Price')
    plt.title('Last 24 Hours Spot Price')
    plt.savefig(f"{config.HOME_DIR}/static/spotprice1D.png")
    plt.close()
   
    plt.plot(points, actual_import )
    plt.xlabel('Record')
    plt.ylabel('Actual Import')
    plt.title('Last 24 Hours Actual Import')
    plt.savefig(f"{config.HOME_DIR}/static/actualimport.png")
    plt.close()

    plt.plot(points, actual_export )
    plt.xlabel('Record')
    plt.ylabel('Actual Export')
    plt.title('Last 24 Hours Actual Export')
    plt.savefig(f"{config.HOME_DIR}/static/actualexport.png")
    plt.close()

    c = conn.cursor()
    c.execute("SELECT spotprice, timestamp from DataPoint where timestamp >= DATE_SUB(NOW(),INTERVAL 5 DAY) AND LEFT(status,5) <> 'ERROR'")
    result = c.fetchall()
    c.close()
    conn.close()

    points.clear()
    spot_prices.clear()

    x=0
    for i in result:
        x += 1
        points.append(x)
        spot_prices.append(i[0])
    
    plt.plot(points, spot_prices)
    plt.xlabel('Record')
    plt.ylabel('Spot Price')
    plt.title('Last 5 Days Spot Price')
    plt.savefig(f"{config.HOME_DIR}/static/spotprice5D.png")
    plt.close()

    plt.boxplot(spot_prices )
    plt.title('Last 5 Days Spot Price')
    plt.savefig(f"{config.HOME_DIR}/static/spotpriceBoxPlot5D.png")
    plt.close()

def create_db_connection():
    conn: None
    try:
        conn = pymysql.connect(
        db=config.DATABASE,    
        user=config.USER,
        passwd=config.PASSWD,
        host='localhost')
    except logging.error as err:
        raise NameError('DatabaseUnavailable')

    return conn

def handle_high_power_demand(status, spot_price, spot_price_avg, power_load, suggested_IE):
    """Handle high power demand"""
    if spot_price <= config.USE_GRID_PRICE:
        status = "Price lower than battery cycle cost"
        logging.info("SPOT PRICE low and demand high")
        suggested_IE = config.IE_MAX_RATE
        charge_from_grid(suggested_IE)
    elif spot_price < spot_price_avg:
        status = f"Price lower than average: {power_load}"
        charge_from_grid(power_load)
    else:
        status = "Price high run on batteries"
        reset_to_default()
    return status

def handle_default_case(
    status, battery_charge, battery_low, battery_full, spot_price, spot_price_avg, power_load
):
    """Handle default case"""
    if is_CPD_period() and spot_price <= spot_price_avg * 1:
        suggested_IE = power_load
        status = "CPD: covering"
        if battery_charge > 50:
            status = "CPD: partial covering"
            suggested_IE = suggested_IE * ((100 - battery_charge) / 100)  # Take the inverse of the battery from the grid if battery is more than half full
        charge_from_grid(suggested_IE)

    else:
        reset_to_default()
        if battery_low:
            status = f"No I/E - Battery Low @ {battery_charge} %"
        elif battery_full:
            status = f"No I/E - Battery Full @ {battery_charge} %"
        else:
            status = f"No I/E - Battery OK @ {battery_charge} %"
    return status

def handle_exception(e):
    error = str(e)
    status = f"ERROR unable to stop I/E {error}"
    logging.error(status)
