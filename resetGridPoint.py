from pymodbus.payload import BinaryPayloadBuilder, Endian
from pymodbus.client.sync import ModbusTcpClient as ModbusClient

client = ModbusClient('192.168.10.30', port='502', auto_open=True, auto_close=True)

def get_battery_charge():
    result = client.read_holding_registers(843)
    return result.registers[0] 
  
def set_grid_point(rate=0):
    rate=rate*0.01
    builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Big)
    builder.reset()
    builder.add_16bit_int(int(rate))
    payload = builder.to_registers()
    print (payload[0])
    client.write_register(2703, payload[0])
    print("Grid @ %s KwH, battery: %s percent", rate, get_battery_charge())
    return