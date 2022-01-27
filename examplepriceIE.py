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
import numpy as np

avg_spot_price= 1.00

calc_discharge_rate(1.20, avg_spot_price)
calc_discharge_rate(1.22, avg_spot_price)
calc_discharge_rate(1.24, avg_spot_price)
calc_discharge_rate(1.26, avg_spot_price)
calc_discharge_rate(1.28, avg_spot_price)
calc_discharge_rate(1.30, avg_spot_price)

