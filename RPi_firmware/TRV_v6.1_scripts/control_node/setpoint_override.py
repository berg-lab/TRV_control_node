# Manual override of TRV setpoint
# Last updated on: 12/18/2019

import sys

sp = 0
_s = sys.argv[1]       # read argument

import os
import time
import json

# set all temporary directories
temp_data_dir = '/home/pi/datalogger/temp_data'
control_node_id_dir = '/home/pi/control_node'
json_dir = '/home/pi/control_node/'

# get node ID
node_ID = [".".join(f.split(".")[:-1]) for f in os.listdir(control_node_id_dir) if f.endswith(".node")]

# read config json file
def load_config():
    attempts = 0
    while attempts < 3:
        try:
            with open(json_dir + 'config.json', 'r') as f:
                data = json.load(f)
            break
        except:
            attempts += 1
            time.sleep(0.1)
    return data

# check config
config = load_config()
setpoint = int(_s)

# for pid_temp and pid_temp_motion only:
if config[0]['acf']['control_strategy'] == 'pid_temp' or config[0]['acf']['control_strategy'] == 'pid_temp_motion':
    if setpoint < 50:
        setpoint = 50
    elif setpoint > 90:
        setpoint = 90

# for all other strategies
else:
    if setpoint < 0:
        setpoint = 0
    elif setpoint > 6:
        setpoint = 6

try:
    file = open('%s/%s.csv' % (temp_data_dir, node_ID[0]),'w')        # save data in file
    file.write("i:%s,y:%s,u:0,w:0" % (node_ID[0], str(setpoint)))
    file.close()
except:
    pass