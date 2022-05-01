########### Python 3.2 #############
import http.client, urllib.request, urllib.parse, urllib.error, base64, time, json, ast, utilfunctions
from datetime import datetime
from pymodbus.constants import Defaults
from pymodbus.constants import Endian
from pymodbus.client.sync import ModbusTcpClient as ModbusClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.payload import BinaryPayloadBuilder, Endian, BinaryPayloadDecoder

DISCHARGE_PRICE=0.20
CHARGE_PRICE=0.02
# CEASE_CHARGE_PRICE=0.12
CHARGE_RATE_KWH=30000
DISCHARGE_RATE_KWH=-10000

Defaults.Timeout = 25
Defaults.Retries = 5
client = ModbusClient('192.168.86.60', port='502', auto_open=True, auto_close=True)

import logging
logging.basicConfig(filename='spot.log', level=logging.INFO, format='%(asctime)s %(message)s')

headers = {
    # Request headers
    'Ocp-Apim-Subscription-Key': 'd53e065901b9410a9ae56900ab16af7e',
}


def get_spot_price():
    now = datetime.now().strftime("%Y-%m-%dT%H:%M")
    # print(now)
    params = urllib.parse.urlencode({
            '$filter': 'PointOfConnectionCode eq \'CML0331\'',
            '&filter': 'TradingDate eq datetime'+now+''
    })
    conn = http.client.HTTPSConnection('emi.azure-api.net')
    conn.request("GET", "/real-time-prices/?%s" % params, "{body}", headers)
    response = conn.getresponse()
    data = response.read()
    json_data = json.loads(data.decode('utf-8'))
    value = json_data[0]['DollarsPerMegawattHour']/1000

    print("%s:Spot price is $%s" %(now, value))
    
    logging.info("Spot price is $%s" ,value)
    conn.close()
    return value


time_to_charge=False
while(1):
    try:
        price=get_spot_price()
        logging.info("Price = %s", price)  
        #logging.info("Price %s and battery charge is %s%s" % (price, get_battery_charge(), str(chr(37))))
            
    except Exception as e:
        logging.warning("[Errior {0}]".format(e))

    time.sleep(60)


####################################