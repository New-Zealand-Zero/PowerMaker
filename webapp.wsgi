#!/usr/bin/env python3

import logging
import sys
logging.basicConfig(stream=sys.stderr)
sys.path.insert(0, '/home/sean/PowerMaker/')
from webapp import app as application
application.secret_key = 'PowerMaker'
