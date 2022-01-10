#!/usr/bin/env python3

# Importing configeration
from datetime import time
import config

# Importing supporting functions
from powermakerfunctions import *

# Importing modules
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    status = get_status()
    # 1, 2, SolarGeneration int, PowerLoad int, BatteryCharge Float, Status varchar(30), Timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP, PRIMARY KEY (RecordID)

    spot_price = float(status[1])   
    avg_spot_price = float(status[2])

    spot_price_str = "{:.4f}".format(spot_price)            
    avg_spot_price_str = "{:.4f}".format(avg_spot_price)   

    export_price = avg_spot_price  + (0.5 * config.SPOT_PRICE_IE_SPREAD)
    import_price = avg_spot_price - (0.5 * config.SPOT_PRICE_IE_SPREAD)
    
    if spot_price > export_price or spot_price < import_price:
        spot_price_color = "lightgreen"
    elif spot_price < import_price:
        spot_price_color = ""

    solar_generation = status[3]
    power_load = status[4]

    if solar_generation  > power_load:
        solar_generation_color = "lightgreen"
    elif spot_price < import_price:
        solar_generation_color = "lightred"

    battery_charge = "{:.1%}".format(status[5]) 
    status_desc = status[6]  
        
    return render_template('index.html', **locals())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')