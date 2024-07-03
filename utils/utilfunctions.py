from re import S

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

# IP Address of the Modbus TCP server in the Forest Lodge Shed? - Check that's correct with Mike
client = ModbusClient('192.168.86.37', port='502', auto_open=True, auto_close=True)

# This function checks if the CONTROL PERIOD STATUS is active - which is a
# period of peak loading on the distribution network.
def is_CPD():
    """check if CONTROL PERIOD STATUS is active - a period of peak loading on distribution network.
    Keyword arguments: None
    """
    result = client.read_holding_registers(3422, unit=1)
    return result.registers[0] == 3

def charge_from_grid(rate_to_charge):
    """ import power from grid
    Keyword arguments: rate to charge
    """
    client.write_register(2703, int(rate_to_charge*0.01 if rate_to_charge > 0 else 1000))
    return
  
def discharge_to_grid(rate_to_discharge):
    """ export power to grid
    Keyword arguments: rate to discharge    
    """
  
    rate_to_discharge=int(rate_to_discharge*0.01)
    builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Big)
    builder.reset()
    builder.add_16bit_int(rate_to_discharge if rate_to_discharge < 0 else -1000)
    payload = builder.to_registers()
    client.write_register(2703, payload[0])  
    
    return