#!/usr/bin/env python3

# Importing configeration
from datetime import time
import config

# Importing supporting functions
from powermakerfunctions import *

# Importing modules
from flask import Flask, render_template, request, redirect

app = Flask(__name__)
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.route('/')
def index():
    status = get_status()
    spot_price_avg, spot_price_min, spot_price_max, import_price, export_price = get_spot_price_stats()
    
    spot_price = float(status[1])   
    avg_spot_price = float(status[2])

    spot_price_str = "{:.4f}".format(spot_price)            
    avg_spot_price_str = "{:.4f}".format(avg_spot_price)
     
    if spot_price > export_price or spot_price < import_price:
        spot_price_color = "lightgreen"

    solar_generation = status[3]
    power_load = status[4]

    if solar_generation  > power_load:
        solar_generation_color = "lightgreen"
    elif spot_price < import_price:
        solar_generation_color = "lightred"

    battery_charge = "{:.1%}".format(status[5]) 
    status_desc = status[6]
    actual_IE = status[7]
    import_price = "{:.4f}".format(import_price)
    export_price = "{:.4f}".format(export_price)

    update_graphs()
        
    return render_template('index.html', **locals())

@app.route('/admin')
def admin():

    status = get_status()
    status_desc = status[6]
    return render_template('admin.html', **locals())

@app.route('/override', methods=['POST'])
def override():
    rate = request.form.get("rate")
    button = request.form.get("button")
    print(rate)
    print(button)
    if (button == 'Apply Manual I/E rate'):
        update_override(True, rate)
    elif (button == 'Automatic I/E'):
        update_override(False, 0)

    return redirect('/admin')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')