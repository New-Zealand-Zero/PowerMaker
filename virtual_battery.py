import sys

import config

import powermakerfunctions
import powermakerNew

import datetime as dt

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Define a convenient object to keep track of the virtual battery
class virtual_battery:

    def __init__(self, 
                 maximum_energy = 250, # kWh
                 current_energy = 125, # kWh 
                 current_discharge = 0, # 
                 current_charge = 0,
                 rte = 0.85):
        
        self.current_energy = current_energy
        self.maximum_energy = maximum_energy
        self.current_soc = current_energy / maximum_energy * 100
        self.current_discharge = current_discharge
        self.current_charge = current_charge
        self.rte = rte

    def update_soc(self,timedelta,# assumed in seconds
                   ):
        
        self.current_energy = self.current_energy - (self.current_discharge - self.current_charge * self.rte) * (timedelta / 3600) / 1000 # converting to hours and kWh
        self.current_soc = self.current_energy / self.maximum_energy * 100

def main():
    
    # Initialise the virtual battery with 50% soc
    vb = virtual_battery(maximum_energy = 250, # kWh
                              current_energy = 125, # kWh
                              rte = 0.85)
    
    datetimestamp_start = dt.datetime(2023,2,10,0,0,0)
    datetimestamp_end = dt.datetime(2023,2,11,0,0,0)
    timestep = 300 # seconds
    
    datetimestamp = datetimestamp_start
    datetimestamps = [datetimestamp]
    
    discharge = []
    charge = []
    soc = []
    
    while datetimestamp <= datetimestamp_end:
       
        # Record the SOC
        soc.append(vb.current_soc)    
        
        # Make decisions based on the current state of the market and the battery
        powermakerNew.sim_vb(datetimestamp = datetimestamp,
                             virtual_battery = vb)
        
        # Record the decisions
        discharge.append(vb.current_discharge)
        charge.append(vb.current_charge)
        
        # Calculate SOC at the the next timestamp
        vb.update_soc(timestep)
        
        # jump forward by time step
        datetimestamp = datetimestamp + dt.timedelta(seconds = timestep)
        datetimestamps.append(datetimestamp)
        
    
    # Add results to a dataframe to be used for revenue calculations
    virtualbattery_dataframe = pd.DataFrame(index = datetimestamps[:-1],
                                            columns = ['Discharge (W)','Charge (W)','State of charge (kWh)'],
                                            data = np.transpose([discharge,charge,soc]))
    
   
    
    # Get final prices 
    columns = ['IntervalStart','IntervalEnd','TradingDate','TradingPeriod', 'DollarsPerMegaWattHour']
    conn = powermakerfunctions.create_db_connection()       
    c = conn.cursor()
    c.execute("SELECT "+','.join(columns)+" from historic_spot_final where IntervalStart >= '"+dt.datetime.strftime(datetimestamp_start,"%Y-%m-%d")+"' and IntervalEnd <= '"+dt.datetime.strftime(datetimestamp_end,"%Y-%m-%d")+"'")
    row = c.fetchall()
    c.close()
    conn.close()
    
    # Create price dataframe
    spot_price = pd.DataFrame(row)
    spot_price.columns = columns
    
    # Loop through each trading interval, check what the battery was doing throughout the 30-min period, calculate revenue based on net discharge / charge against the energy price
    net_revenue = 0
    for interval_start, interval_end, price in zip(spot_price['IntervalStart'].values,spot_price['IntervalEnd'].values,spot_price['DollarsPerMegaWattHour'].values):
        
        # Grab the battery setpoints for this interval. Add buffer incase dispatch is not perfectly aligned with the NZEM trading intervals
        interval_start = np.datetime64(interval_start)
        interval_end = np.datetime64(interval_end)
        current_setpoints = virtualbattery_dataframe.loc[(virtualbattery_dataframe.index >= interval_start - np.timedelta64(timestep, 's')) & (virtualbattery_dataframe.index <= interval_end + np.timedelta64(timestep, 's')),:]
        
        # If there's a misalignment in dispatch, grab the dispatch closest to interval_start and then define it at interval_start
        interval_start_setpoints = (current_setpoints.loc[current_setpoints.index <= interval_start]).iloc[[-1],:]
        interval_end_setpoints = (current_setpoints.loc[current_setpoints.index >= interval_end]).iloc[[0],:]
        
        # Cut off the top and tile of the window to add in the values at start and end
        current_setpoints = virtualbattery_dataframe.loc[(virtualbattery_dataframe.index > interval_start) & (virtualbattery_dataframe.index < interval_end ),:]
        
        interval_start_setpoints.index = [interval_start]
        interval_end_setpoints.index = [interval_end]
        
        current_setpoints = pd.concat([interval_start_setpoints,
                                       current_setpoints,
                                       interval_end_setpoints])
        
        # Calculate net charge and discharge at the point of connection
        net_discharge = sum(discharge/(10**6) * (next_time - current_time).seconds / (60*60) for discharge,current_time, next_time in zip(current_setpoints['Discharge (W)'].values[:-1],current_setpoints.index[:-1],current_setpoints.index[1:])) # in MWh
        net_charge = sum(charge/(10**6) * (next_time - current_time).seconds / (60*60) for charge,current_time, next_time in zip(current_setpoints['Charge (W)'].values[:-1],current_setpoints.index[:-1],current_setpoints.index[1:])) # in MWh
        
        # Calculate net spot revenue
        net_revenue = net_revenue + (net_discharge - net_charge) * price
    
    # Plotting for testing
    """
    plt.plot(soc)
    plt.figure()
    plt.plot(discharge)
    plt.plot(charge)
    
    conn = powermakerfunctions.create_db_connection()       
    c = conn.cursor()
    c.execute("SELECT DollarsPerMegaWattHour from historic_spot where PublishDateTime >= '"+dt.datetime.strftime(datetimestamp_start,"%Y-%m-%dT%H:%M:%S")+"' and PublishDateTime <= '"+dt.datetime.strftime(datetimestamp_end,"%Y-%m-%dT%H:%M:%S")+"'")
    row = c.fetchall()
    #print(row)
    c.close()
    conn.close()
    
    spot_price = row
    
    plt.figure()
    plt.plot(spot_price)
    """
    
if __name__ == "__main__":
    main()