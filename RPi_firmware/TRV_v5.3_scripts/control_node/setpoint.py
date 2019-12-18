# Manual override of TRV setpoint
# Last updated on: 11/5/2018

import sys

sp = 0
_s = sys.argv[1]       # read argument

import os
temp_data_dir = '/home/pi/datalogger/temp_data'
control_node_id_dir = '/home/pi/control_node'

# temp_data = [".".join(f.split(".")[:-1]) for f in os.listdir(temp_data_dir)]    # list of all temp data files
node_ID = [".".join(f.split(".")[:-1]) for f in os.listdir(control_node_id_dir) if f.endswith(".node")]    # get node ID

try:
    file = open('%s/%s.csv' % (temp_data_dir, node_ID[0]),'w')
    file.write("i:%s,y:%s,u:0" % (node_ID[0], str(_s)))
    file.close()
except:
    pass
