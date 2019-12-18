# -*- coding: utf-8 -*-

# This script checks the last state of motion detected
# and changes the setpoint of control valve accordingly
# It also allows for auto scripts to run uninterrupted

# Developed by Akram Ali
# Last updated on: 2/18/2019

import time
import os

time.sleep(5)   # wait a bit so other scripts can start running first

temp_data_dir = '/home/pi/datalogger/temp_data'
control_node_id_dir = '/home/pi/control_node'
node_ID = [".".join(f.split(".")[:-1]) for f in os.listdir(control_node_id_dir) if f.endswith(".node")]    # get node ID

# get latest motion status from file
def readMotion():
    try:
        file = open('%s/%d.csv' % (temp_data_dir, int(node_ID[0])+2),'r')        # get data from motion node file
        data = file.readline()
        file.close()
    except:
        return 0
    parsed_data = {}
    try:
        for p in data.strip().split(","): #strip() removes trailing \n
            k,v = p.split(":")
            parsed_data[k] = v if v else 0.00
        motion = parsed_data.get('m')
        return motion
    except:
        return 0

# check control node
def readControlnode():
    try:
        file = open('%s/%s.csv' % (temp_data_dir, node_ID[0]),'r')        # get data from control file
        data = file.readline()
        file.close()
    except:
        return 0, 0
    parsed_data = {}
    try:
        for p in data.strip().split(","): #strip() removes trailing \n
            k,v = p.split(":")
            parsed_data[k] = v if v else 0.00
        s = parsed_data.get('y')
        u = parsed_data.get('u')
        return s, u
    except:
        return 0, 0

# write setpoint
def writeSetpoint(sp):
    try:
        file = open('%s/%s.csv' % (temp_data_dir, node_ID[0]),'w')
        file.write("i:%s,y:%s,u:0" % (node_ID[0], str(sp)))
        file.close()
    except:
        pass

# get latest temperature reading from file
def readTemperature():
    try:
        file = open('%s/%d.csv' % (temp_data_dir, int(node_ID[0])+1),'r')        # get data from temp node file
        data = file.readline()
        file.close()
    except:
        return 0
    parsed_data = {}
    try:
        for p in data.strip().split(","): #strip() removes trailing \n
            k,v = p.split(":")
            parsed_data[k] = v if v else 0.00
        temp = parsed_data.get('t')
        return temp
    except:
        return 0

# check motion forever
while True:
    try:
        file = open('auto.csv','r')
        auto = file.readline()
        file.close()
    except:
        pass

    if auto == '0':     # auto not set, continue
        motion = readMotion()
        current_time = time.time()      # get current time
        try:
            last_motion_time = os.path.getmtime('%s/%d.csv' % (temp_data_dir, int(node_ID[0])+2))      # get last date modified of m.csv
        except:
            last_motion_time = 0

        elapsed_time = current_time - last_motion_time

        if motion == '0':     # if no motion detected
            try:
                file = open('m.csv','w')
                file.write(str(elapsed_time))    # save last motion time
                file.close()
            except:
                pass
            if elapsed_time >= 3600:     # check if 60 mins have passed
                s = 0       # new setpoint is 0
                writeSetpoint(s)
            else:
                pass

        elif motion == '1':     # if motion detected
            s, u = readControlnode()
            if u == '1':    # if there was manual override
                pass    # don't do anything
            else:   # no manual override yet
                try:
                    file = open('m.csv','r')        # get last elapsed time when motion was 0
                    previous_elapsed_time = float(file.readline())
                    file.close()
                except:
                    pass

                if previous_elapsed_time >= 3600:     # check if 60 mins have passed
                    t = float(readTemperature())
                    if t < 21:   # if temperature below 70 F
                        s = 4       # new setpoint is 4
                        try:
                            file = open('%s/%s.csv' % (temp_data_dir, node_ID[0]),'w')
                            file.write("i:%s,y:%s,u:0" % (node_ID[0], str(s)))
                            file.close()
                        except:
                            pass
                else:
                    pass

    elif auto == '1':     # auto set, pass
        pass

    time.sleep(5) # check motion every 5 seconds
