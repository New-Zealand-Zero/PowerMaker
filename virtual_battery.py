import sys

import config

import powermakerfunctions
import powermakerNew

import datetime as dt

import matplotlib.pyplot as plt

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
    
    discharge = []
    charge = []
    soc = []
    
    while datetimestamp <= datetimestamp_end:
        print(datetimestamp)
        # Update energy (this does nothing on the first loop)
        vb.update_soc(timestep)
        
        # Make decisions based on the current state of the market and the battery
        powermakerNew.sim_vb(datetimestamp = datetimestamp,
                             virtual_battery = vb)
        
        datetimestamp = datetimestamp + dt.timedelta(seconds = timestep)
        
        discharge.append(vb.current_discharge)
        charge.append(vb.current_charge)
        soc.append(vb.current_soc)
    
    # Plotting for testing
    
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
    
    
if __name__ == "__main__":
    main()