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

Defaults.Timeout = 25
Defaults.Retries = 5
client = ModbusClient(config.MODBUS_CLIENT_IP, port='502', auto_open=True, auto_close=True)

def get_spot_price():
    """return the latest power spotprice from OCP
     Keyword arguments: None
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    #if generate testing data if not in Production
    if (not config.PROD):
            spot_price = float("{0:.5f}".format(random.uniform(0.00001, 0.09)))
            if (spot_price > .08):
                spot_price = spot_price + float("{0:.5f}".format(random.uniform(100, 500)))
            logging.info(f"spot price ${spot_price}")
            return spot_price

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
    logging.info(f"SPOT PRICE:${spot_price}")
    conn.close()
    return spot_price

def get_battery_low():
    """return true if battery is low
     Keyword arguments: None
    """
    battery_low = get_battery_charge() <= config.LOW_BATTERY_THRESHOLD
    logging.info(f"Battery low:{battery_low}")
    return battery_low

def get_battery_full():
    """return true if battery is full
     Keyword arguments: None
    """
    battery_full = get_battery_charge() >= config.CHARGED_BATTERY_THRESHOLD
    logging.info(f"Battery full:{battery_full}")
    return battery_full

def get_battery_charge():
    """return the battery charge
     Keyword arguments: None
    """
    if (config.PROD):  
        result = client.read_holding_registers(843)
        battery_charge= result.registers[0]
    else:
         battery_charge=  float("{0:.1f}".format(random.uniform(1, 100)))

    return battery_charge

def reset_to_default():
    if (config.PROD):
        client.write_register(2700,int(0))

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

def charge_from_grid(rate_to_charge=0):
    """ import power from grid
    Keyword arguments: rate to charge
    """

    if (config.PROD):
        client.write_register(2700, int(rate_to_charge if rate_to_charge > 0 else config.CHARGE_RATE_KWH))

    logging.info("Importing from Grid @ %s KwH, battery: %s percent", rate_to_charge if rate_to_charge > 0 else config.CHARGE_RATE_KWH, get_battery_charge())
    return
  

def discharge_to_grid(rate_to_discharge=0):
    """ export power to grid
    Keyword arguments: rate to discharge
    """
    if (config.PROD):
        builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Big)
        builder.reset()
        builder.add_16bit_int(rate_to_discharge if rate_to_discharge < 0 else config.DISCHARGE_RATE_KWH)
        payload = builder.to_registers()
        client.write_register(2700, payload[0])

    # logging.info("Exporting to Grid @ %s KwH, battery: %s percent", rate_to_discharge if rate_to_discharge < 0 else config.DISCHARGE_RATE_KWH, get_battery_charge())
    logging.info(f"Exporting to Grid @ {rate_to_discharge} KwH, battery: {get_battery_charge()} percent" )
    return

def charging_time():
    """ calculate time required to charge
    Keyword arguments: None
    """
    now = datetime.now().time()
    on_time = time(0,5)
    off_time = time(3,5)
    logging.info(f"Charging Time {on_time < now} {now < off_time}" )
    return on_time < now and now < off_time

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

def get_avg_spot_price():
    """return average spot price
    Keyword arguments: None
    """  
    import pymysql
    conn = pymysql.connect(
    db=config.DATABASE,    
    user=config.USER,
    passwd=config.PASSWD,
    host='localhost')

    c = conn.cursor()
    c.execute("SELECT AVG(SpotPrice) from DataPoint where Timestamp > now() - interval 5 day")
    row = c.fetchone()
    if row[0] == None:
        avg_spot_price = get_spot_price()
    else:
        avg_spot_price = row[0]
    c.close()
    conn.close()

    logging.info(f"Average Spot Price {avg_spot_price}")
    return avg_spot_price

def get_status():
    """return current status
    Keyword arguments: None
    """  
    import pymysql
    conn = pymysql.connect(
    db=config.DATABASE,    
    user=config.USER,
    passwd=config.PASSWD,
    host='localhost')

    c = conn.cursor()
    c.execute("SELECT * from DataPoint where RecordID = (SELECT Max(RecordID) from DataPoint)")
    row = c.fetchone()
    print(row)
    c.close()
    conn.close()

    return row


#get_spot_price()
#get_avg_spot_price()
#battery_low()
#battery_full()
#is_CPD()
#charge_from_grid()
#discharge_to_grid()
#charging_time()
#get_solar_generation()
#get_existing_load()
# get_status()S