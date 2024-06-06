import requests
import http
import datetime as dt
import json
import pandas as pd
import pymysql
from sqlalchemy import create_engine
import sys
import time
import logging

sys.path.append('../')

from powermakerfunctions import create_db_connection
import config

r = requests.post('https://api.electricityinfo.co.nz/login/oauth2/token', json={
    "grant_type": "client_credentials",
    "client_id": 'Ubr1lMj299t7ZbHtlB7FhGjSFM5m79JP',
    "client_secret": '3ETh13MW1gNrbZ7SLnhYQtdsjdk6j1dd',
})

access_token = r.json().get('access_token')

print(access_token)

conn = http.client.HTTPSConnection("api.electricityinfo.co.nz")
headers = {'accept': "application/json",
           'Authorization': 'Bearer %s' % access_token}

# conn.request("GET", "/api/market-prices/v1/schedules", headers=headers)

# res = conn.getresponse()
# data = res.read()

# print(data.decode("utf-8"),"\n")

# conn.request("GET", "", headers=headers)

# res = conn.getresponse()
# data = res.read()

# print(data.decode("utf-8"),"\n")

# # conn.request("GET", "/api/market-prices/v1/prices?schedules=RTP&marketType=R&nodes=%CML0331&from=&to=&back=&forward=&offset=", headers=headers)

# # res = conn.getresponse()
# # data = res.read()

# # print("this is the one \n",data.decode("utf-8"),"\n")

now = dt.datetime(2023,3,1)#dt.datetime.now() - dt.timedelta(minutes=1)

startday = dt.datetime(2023,1,1) - dt.timedelta(minutes = 10)
node = 'CML0331'

rtd_prices = pd.DataFrame()

for day in range((now - startday).days):

    currentday = startday+dt.timedelta(days=day)
    
    currentday_str = dt.datetime.strftime(currentday,"%Y%m%d")
    
    print("https://www.emi.ea.govt.nz/Wholesale/Datasets/DispatchAndPricing/DispatchEnergyPrices/"+str((currentday).year)+"/"+currentday_str+"_DispatchEnergyPrices.csv")
    
    # EMI link (WITS API only keeps data to -7 days for RTD, not useful enough here)
    while True:
        try:
            currentday_data = pd.read_csv("https://www.emi.ea.govt.nz/Wholesale/Datasets/DispatchAndPricing/DispatchEnergyPrices/"+str((currentday).year)+"/"+currentday_str+"_DispatchEnergyPrices.csv")
            break
        except Exception as e:
            
            print("Exception: "+str(e))
            time.sleep(60)    
    
    currentday_data = currentday_data.loc[(currentday_data['IsProxyPriceFlag']=='N') & (currentday_data['PointOfConnection']==node),['TradingDate','TradingPeriod','PublishDateTime','DollarsPerMegawattHour']]
    
    currentday_data = currentday_data.reset_index(drop=True)
    
    rtd_prices =  pd.concat([rtd_prices,currentday_data])


rtd_prices  = rtd_prices.reset_index(drop=True)

# Convert strings to datetime

rtd_prices['PublishDateTime'] = pd.to_datetime(rtd_prices['PublishDateTime'])

engine = create_engine('mysql+pymysql://pm:pm@localhost/pm')

rtd_prices.to_sql('historic_spot',con =  engine, if_exists='replace',index=False)

#conn.close()