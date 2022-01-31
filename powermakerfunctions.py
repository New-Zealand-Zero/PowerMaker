#!/usr/bin/env python3
"""PowerMaker functions
    get_spot_price()
    get_avg_spot_price()
    get_battery_low()
    get_battery_full()
    get_solar_generation()
    get_existing_load()       
    is_CPD()
    charge_from_grid()
    discharge_to_grid()
    charging_time()
"""

# Importing configeration
from re import S
import config

# Importing modules
from datetime import datetime, time # obtain and format dates and time
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

# Log to file in production on screen for test
logging.basicConfig(level=logging.INFO, format='%(asctime)s TEST %(message)s') 

if (config.PROD):
    client = ModbusClient('192.168.86.37', port='502', auto_open=True, auto_close=True)

def get_spot_price():
    """return the latest power spotprice from OCP
     Keyword arguments: None
    """
    spot_price =0
    if (config.PROD):
        now = datetime.now().strftime("%Y-%m-%dT%H:%M")
        Defaults.Timeout = 25
        Defaults.Retries = 5
        params = urllib.parse.urlencode({
                '$filter': 'PointOfConnectionCode eq \'CML0331\'',
                '&filter': 'TradingDate eq datetime'+now+''
        })
        request_headers = {
        'Ocp-Apim-Subscription-Key': config.OCP_APIM_SUBSCRIPTION_KEY
        }
        conn = http.client.HTTPSConnection('emi.azure-api.net')
        conn.request("GET", "/real-time-prices/?%s" % params, "{body}", request_headers)
        response = conn.getresponse()
        data = response.read()
        json_data = json.loads(data.decode('utf-8'))
        spot_price = json_data[0]['DollarsPerMegawattHour']/1000 
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

def get_battery_status():
    """return the battery charge and status
     Keyword arguments: None
    """
    # client = ModbusClient('192.168.86.37', port='502', auto_open=True, auto_close=True)

    if (config.PROD):  
        result = client.read_holding_registers(843)
        battery_charge= int(result.registers[0])
    else:
        battery_charge=  int("{0:.3f}".format(random.uniform(0.1, 1)))

    battery_low = battery_charge <= config.LOW_BATTERY_THRESHOLD
    battery_full = battery_charge >= config.CHARGED_BATTERY_THRESHOLD

    logging.info(f"Battery: {battery_charge} %" )
    return battery_charge, battery_low, battery_full

def reset_to_default():
    if (config.PROD):
        client.write_register(2703,int(0))

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
        if (random.randint(1, 10) > 9):
            logging.info("CPD ACTIVE")
            return True
        else:
            logging.info("CPD INACTIVE")
            return False

def charge_from_grid(rate_to_charge):
    """ import power from grid
    Keyword arguments: rate to charge
    """

    if (config.PROD):
        client.write_register(2703, int(rate_to_charge if rate_to_charge > 0 else config.CHARGE_RATE_KWH))
   
    logging.info(f"Importing from Grid @ {rate_to_charge} KwH" )
    return
  
def discharge_to_grid(rate_to_discharge):
    """ export power to grid
    Keyword arguments: rate to discharge
    """
    logging.info(f"Suggested export to Grid @ {rate_to_discharge/1000} kWh" )
    if (config.PROD):
        rate_to_discharge=int(rate_to_discharge*0.1)
        builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Big)
        builder.reset()
        builder.add_16bit_int(rate_to_discharge if rate_to_discharge < 0 else config.DISCHARGE_RATE_KWH)
        payload = builder.to_registers()
        client.write_register(2703, payload[0])  
    
    return

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

def get_existing_load():
    """return current power load
    Keyword arguments: None
    """    
    if (config.PROD):    
        power_load = client.read_holding_registers(817).registers[0]
        power_load += client.read_holding_registers(818).registers[0]
        power_load += client.read_holding_registers(819).registers[0]
    else:
        power_load= random.randint(5000, 10000)

    logging.info(f"Power Load {power_load}")
    return power_load
    
def get_actual_IE():
    """return current power load
    Keyword arguments: None
    """    
    #client = ModbusClient('192.168.86.37', port='502', auto_open=True, auto_close=True)

    if (not config.PROD):    
        power_load = client.read_holding_registers(2600).registers[0]
        power_load += client.read_holding_registers(2601).registers[0]
        power_load += client.read_holding_registers(2602).registers[0]
    else:
        power_load= random.randint(-config.IE_MAX_RATE, config.IE_MAX_RATE)
 
    logging.info(f"Actual IE {power_load}")
    return power_load

def get_spot_price_stats():
    """return average spot price
    Keyword arguments: None
    """  
    conn = create_db_connection()
    c = conn.cursor()
    c.execute("SELECT SpotPrice from DataPoint where Timestamp > now() - interval 5 day")
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
        spot_price_lq=np.quantile(spot_prices,config.IMPORT_QUANTILE)
        spot_price_uq=np.quantile(spot_prices,config.EXPORT_QUANTILE)
    else:
        spot_price_avg=0
        spot_price_min=0
        spot_price_max=0
        spot_price_lq=0
        spot_price_uq=0
    
    logging.info(f"Average Spot Price {spot_price_avg}")
    return spot_price_avg, spot_price_min, spot_price_max, spot_price_lq, spot_price_uq

def get_status():
    """return current status
    Keyword arguments: None
    """      
    conn = create_db_connection()
    c = conn.cursor()
    c.execute("SELECT * from DataPoint where RecordID = (SELECT Max(RecordID) from DataPoint)")
    row = c.fetchone()
    print(row)
    c.close()
    conn.close()

    return row

def get_override():
    """return if manual overide state
    Keyword arguments: None
    """      
    conn = create_db_connection()
    c = conn.cursor()
    c.execute("SELECT ConfigValue from Config where ConfigID = 'Override'")
    row = c.fetchone()
    c.close()
    conn.close()
   
    if (row[0] == "N"):
        return False, 0
    else:
        return True, 100
                # return True, int(row[0])

def update_override(overide, rate):
    conn = create_db_connection()
    c = conn.cursor()
    if (overide):
        c.execute(f"UPDATE Config SET ConfigValue = {rate} where ConfigID = 'Override'")
    else:
        c.execute(f"UPDATE Config SET ConfigValue = 'N' where ConfigID = 'Override'")
    conn.commit()
    c.close()
    conn.close()

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
    c.execute("SELECT spotprice, actualIE from DataPoint where timestamp >= DATE_SUB(NOW(),INTERVAL 4 HOUR)")
    result = c.fetchall()
    c.close()  
    conn.close()

    points = []
    spot_prices = []
    actual_IE = []

    x=0
    for i in result:
        x += 1
        points.append(x)
        spot_prices.append(i[0])
        actual_IE.append(i[1])

    plt.plot(points, spot_prices)
    plt.xlabel('Record')
    plt.ylabel('Spot Price')
    plt.title('Last 4 Hours Spot Price')
    plt.savefig(f"{config.HOME_DIR}/static/spotprice.png")
  
    plt.plot(points, actual_IE )
    plt.xlabel('Record')
    plt.ylabel('Actual IE')
    plt.title('Last 4 Hours Actual IE')
    plt.savefig(f"{config.HOME_DIR}/static/actualIE.png")
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
        print(f"Error: '{err}'")

    return conn

def 

# update_override(False, None)
# print(get_override())
#print( get_spot_price())
# get_avg_spot_price()
# print(get_battery_status())
# is_CPD()
# print(get_battery_charge())
# charge_from_grid()
# discharge_to_grid()
# charging_time()
#
# print(get_solar_generation())
# get_existing_load()
# get_status()
# print(calc_charge_rate(1,1,0))
# update_graphs()
# print(get_spot_price_stats())
# print(get_actual_IE())
#print(get_battery_status())

