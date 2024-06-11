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
from dateutil.relativedelta import relativedelta

sys.path.append('../')

from powermakerfunctions import create_db_connection
import config



now = dt.datetime(2023,3,1)#dt.datetime.now() - dt.timedelta(minutes=1)

startday = dt.datetime(2023,1,1) - dt.timedelta(minutes = 10)
node = 'CML0331'

final_prices = pd.DataFrame()
rtd_prices = pd.DataFrame()

# Getting RTD
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


# Getting FINAL prices 

# get final prices for the same time period
start_month = [startday+ dt.timedelta(minutes = 10)]
end_month = []

while start_month[-1] <= now:
    end_month.append(start_month[-1] + relativedelta(months=1))
    start_month.append(end_month[-1]+relativedelta(days=1))

for month in start_month:
    
    month_string = dt.datetime.strftime(month,"%Y%m")
    
    # EMI link (WITS API only keeps data to -7 days for RTD, not useful enough here)
    while True:
        try:
            currentmonth_data = pd.read_csv("https://www.emi.ea.govt.nz/Wholesale/Datasets/DispatchAndPricing/FinalEnergyPrices/ByMonth/"+month_string+"_FinalEnergyPrices.csv")
            break
        except Exception as e:
            
            print("Exception: "+str(e))
            time.sleep(60)    
    
    currentmonth_data = currentmonth_data.loc[(currentmonth_data['PointOfConnection']==node),['TradingDate','TradingPeriod','DollarsPerMegawattHour']]
    
    
    currentmonth_data['IntervalStart'] = [dt.datetime.strptime(date,"%Y-%m-%d") + dt.timedelta(minutes = int(30*(time-1))) for date, time in zip(currentmonth_data['TradingDate'].values,currentmonth_data['TradingPeriod'].values)]
    currentmonth_data['IntervalEnd'] = [dt.datetime.strptime(date,"%Y-%m-%d") + dt.timedelta(minutes = int(30*(time))) for date, time in zip(currentmonth_data['TradingDate'].values,currentmonth_data['TradingPeriod'].values)]
    
    currentmonth_data = currentmonth_data.reset_index(drop=True)
    
    final_prices =  pd.concat([final_prices,currentmonth_data])

engine = create_engine('mysql+pymysql://pm:pm@localhost/pm')

rtd_prices.to_sql('historic_spot',con =  engine, if_exists='replace',index=False)
final_prices.to_sql('historic_spot_final',con =  engine, if_exists='replace',index=False)

#conn.close()