#!/usr/bin/env python3

# Importing configeration
from datetime import time
import config

# Importing supporting functions
from powermakerfunctions import *

# Importing modules
import logging # flexible event logging
import math # mathematical functions
from time import sleep  # To add delay
import matplotlib.pyplot as plt

x = [10,20,30,40,50]
y = [1000,1125,1846,5996,29877]
 
# plotting the points
plt.plot(x, y)
 
# naming the x axis
plt.xlabel('margin')
# naming the y axis
plt.ylabel('discharge')
 
# giving a title to my graph
plt.title('exp')
 
# function to show the plot
plt.show()