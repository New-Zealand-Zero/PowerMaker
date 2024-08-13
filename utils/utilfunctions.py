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
import config

client = ModbusClient(config.MODBUS_CLIENT_IP, port='502', auto_open=True, auto_close=True)

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
    upper, lower = split_into_ushorts(rate_to_charge)

    client.write_register(2703, upper, unit=1)
    client.write_register(2704, lower, unit=1)
    return
  
def discharge_to_grid(rate_to_discharge):
    """ export power to grid
    Keyword arguments: rate to discharge    
    """
    max_int_32 = 2 ** 31 - 1
    upper, lower = split_into_ushorts(max_int_32 - rate_to_discharge)

    client.write_register(2703, upper, unit=1)
    client.write_register(2704, lower, unit=1)
    return


def split_into_ushorts(number):
    if not (0 <= number < 2 ** 32):
        raise ValueError("Number must be between 0 and 4294967295 (inclusive).")

    lower_ushort = number & 0xFFFF
    upper_ushort = (number >> 16) & 0xFFFF

    return upper_ushort, lower_ushort