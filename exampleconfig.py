#Env
PROD = False
OCP_APIM_SUBSCRIPTION_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxx"
LOW_BATTERY_THRESHOLD=0.25
CHARGED_BATTERY_THRESHOLD=0.75
MODBUS_CLIENT_IP = "192.168.1.x"
DELAY = 1                 # Pause between updating the status
HOME_DIR = "/home/user/PowerMaker"
SERVER_IP = "192.168.1.1"

#Database connection
DATABASE = "pm"
USER = "pm"
HOST= "localhost"
PASSWD = "pm"

#Spot price
IMPORT_QUANTILE = .25     # If the spot price is in a range below quantile import power. Default upper quartile
EXPORT_QUANTILE = .75     # If the spot price is in a range above this quantile export power. Default lower quartile
EXP_INPUT_MIN = 0         # Starting point for exp function to be applied
EXP_INPUT_MAX = 4         # End point for exp function to be applied
IE_MIN_RATE = 1000        # Min rate for power to be I/E
IE_MAX_RATE = 120000      # Max rate for power to be I/E
LOW_PRICE_IMPORT = 0.01   # Override low price import, at this price or less import power
MIN_MARGIN = 0.14         # Minium margin vs 5 day average required before I/E, consider battery cycle costs in setting this valve
HALF_MIN_MARGIN = MIN_MARGIN / 2 
