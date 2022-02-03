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
    suggested_IE = status[9]
    import_price = "{:.4f}".format(import_price)
    export_price = "{:.4f}".format(export_price)

    update_graphs()
        
    return render_template('index.html', **locals())

@app.route('/admin')
def admin():

    remote_ip_address = request.remote_addr
    remote_ip_address_list = remote_ip_address.split(".")
    server_ip_list = config.SERVER_IP.split(".")

    if (server_ip_list[0] == remote_ip_address_list[0] and server_ip_list[1] == remote_ip_address_list[1] and server_ip_list[2] == remote_ip_address_list[2]):
        status = get_status()
        status_desc = status[6]
        return render_template('admin.html', **locals())
    else:
        return redirect('/')

@app.route('/override', methods=['POST'])
def override():
    rate = request.form.get("rate")
    button = request.form.get("button")
    if (button == 'Apply Manual I/E rate'):
        update_override(True, rate)
    elif (button == 'Automatic I/E'):
        update_override(False, 0)

    return redirect('/admin')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')