#env constants
PROD = False
OCP_APIM_SUBSCRIPTION_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxx"
LOW_BATTERY_THRESHOLD=25
CHARGED_BATTERY_THRESHOLD=75
CHARGE_RATE_KWH=25000
DISCHARGE_RATE_KWH=-10000
CPD_DISCHARGE_RATE=-1000
MAXIMUM_CHARGE_PRICE=0.6
MINIMUM_DISCHARGE_PRICE=0.35
LOW_BATTERY_THRESHOLD=25
CHARGED_BATTERY_THRESHOLD=75
MODBUS_CLIENT_IP = "192.168.1.xxx"
#Database connection constants
DATABASE = "pm"
USER = "pm"
HOST= "localhost"
PASSWD = "pm"
#Spot price constants
SPOT_PRICE_IE_SPREAD = 0.40 # spread between import and exporting compared to 5 days average
MARGIN_MIN = 10             # At this price point about the avg spot price I/E at the min I/E rate
MARGIN_MAX = 40             # At this price point about the avg spot price I/E at the min I/E rate
MIN_EXP_VALUE = 0           # Starting point for exp function to be applied
MAX_EXP_VALUE = 7           # End point for exp function to be applied
IE_MIN_RATE = 1000          # Min rate for power to be I/E
IE_MAX_RATE = 30000         # Max rate for power to be I/E