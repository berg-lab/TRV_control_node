# -*- coding: utf-8 -*-

# This script enforces a scheduled operation of control valve
# It checks time and changes the setpoint of control valve accordingly

# Developed by Akram Ali
# Last updated on: 12/4/2018

from datetime import datetime
import time
import os

time.sleep(10)  # give enough time for all other scripts to come up before executing this one

temp_data_dir = '/home/pi/datalogger/temp_data'
control_node_id_dir = '/home/pi/control_node'
node_ID = [".".join(f.split(".")[:-1]) for f in os.listdir(control_node_id_dir) if f.endswith(".node")]    # get node ID
auto = 0
u = 0
s = 0

# create auto.csv file with auto value initialized to 0
try:
    file = open('auto.csv','w')
    file.write('0')     # write 1 to indicate schedule is enforced - valve open
    file.close()
except:
    pass


while True:
    now = datetime.now()   # get current date/time
    hr = now.hour       # get current hour
    min = now.min
    if (7 <= hr < 17):     # check if time is between 7:00 AM and 5:00 PM
        try:
            file = open('auto.csv','r')
            auto = file.readline()
            file.close()
        except:
            pass

        if auto == '0':     # auto not set, continue
            s = 4   # new setpoint is now 4
            try:
                file = open('%s/%s.csv' % (temp_data_dir, node_ID[0]),'w')
                file.write("i:%s,y:%s,u:0" % (node_ID[0], str(s)))
                file.close()
            except:
                pass
            try:
                file = open('auto.csv','w')
                file.write('1')     # write 1 to indicate schedule is enforced - valve open
                file.close()
            except:
                pass
        elif auto == '1':
            pass

    elif (hr >= 17 or hr < 7):      # check if time is between 5 PM and 8 AM (next day)
        try:
            file = open('auto.csv','r')
            auto = file.readline()
            file.close()
        except:
            pass

        if auto == '1':     # auto not set, continue
            s = 0   # new setpoint is now 0
            try:
                file = open('%s/%s.csv' % (temp_data_dir, node_ID[0]),'w')
                file.write("i:%s,y:%s,u:0" % (node_ID[0], str(s)))
                file.close()
            except:
                pass
            try:
                file = open('auto.csv','w')
                file.write('0')     # write 0 to indicate schedule is enforced - valve closed
                file.close()
            except:
                pass

        elif auto == '0':
            try:
                file = open('%s/%s.csv' % (temp_data_dir, node_ID[0]),'r')        # get data from control file
                data = file.readline()
                file.close()
            except:
                pass
            parsed_data = {}
            try:
                for p in data.strip().split(","): #strip() removes trailing \n
                    k,v = p.split(":")
                    parsed_data[k] = v if v else 0.00
                u = parsed_data.get('u')        # get manual override status
                s = parsed_data.get('y')        # get setpoint
            except:
                pass
            if u == '1':    # if there was manual override
                current_time = time.time()      # get current time
                last_override_time = os.path.getmtime('%s/%d.csv' % (temp_data_dir, int(node_ID[0])))      # get last date modified of node
                if current_time - last_override_time >= 1800:     # check if 30 mins have passed
                    s = 0   # new setpoint is now 0
                    try:
                        file = open('%s/%s.csv' % (temp_data_dir, node_ID[0]),'w')
                        file.write("i:%s,y:%s,u:0" % (node_ID[0], str(s)))
                        file.close()
                    except:
                        pass
                else:
                    pass

    time.sleep(60) # check every min
