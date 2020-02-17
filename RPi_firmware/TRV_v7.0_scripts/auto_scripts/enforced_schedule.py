# -*- coding: utf-8 -*-

# This script enforces a scheduled operation of control valve
# It checks time and changes the setpoint of control valve accordingly

# Developed by Akram Ali
# Last updated on: 02/17/2020

from datetime import datetime
import time
import json
import os

time.sleep(10)  # give enough time for all other scripts to come up before executing this one

temp_data_dir = '/home/pi/datalogger/temp_data'
control_node_id_dir = '/home/pi/control_node'
json_dir = '/home/pi/control_node/'

node_ID = [".".join(f.split(".")[:-1]) for f in os.listdir(control_node_id_dir) if f.endswith(".node")]    # get node ID

auto = 0
u = 0
s = 4   # by default, setpoint for enforced schedule is 4
enforced_schedule_start_time = '7:00'
enforced_schedule_end_time = '17:00'
enforced_schedule_override_time = '30'  # default override timeout in minutes

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

# read existing PWM value
def read_control_values():
    try:
        file = open('%s/%s.csv' % (temp_data_dir, node_ID[0]),'r')
        data = file.readline()
        file.close()
    except:
        return 0
    parsed_data = {}
    try:
        for p in data.strip().split(","): #strip() removes trailing \n
            k,v = p.split(":")
            parsed_data[k] = v if v else 0.00
        u = parsed_data.get('u')        # get manual override status
        s = parsed_data.get('y')        # get setpoint
        w = parsed_data.get('w')        # get PWM
        return s, u, w
    except:
        pass

# create auto.csv file with auto value initialized to 0
try:
    file = open('auto.csv','w')
    file.write('0')     # write 1 to indicate schedule is enforced - valve open
    file.close()
except:
    pass


while True:
    # read latest config from file
    config = load_config()
    if config[0]['acf']['control_strategy'] == 'enforced_schedule':
        setpoint = config[0]['acf']['enforced_schedule_setpoint']
        enforced_schedule_start_time = config[0]['acf']['enforced_schedule_start_time']
        enforced_schedule_end_time = config[0]['acf']['enforced_schedule_end_time']
        enforced_schedule_override_time = config[0]['acf']['enforced_schedule_override_time']

        start_hour = datetime.strptime(enforced_schedule_start_time, '%H:%M').hour
        end_hour = datetime.strptime(enforced_schedule_end_time, '%H:%M').hour
    
    now = datetime.now()   # get current date/time
    hr = now.hour       # get current hour
    min = now.min
    if (start_hour <= hr < end_hour):     # check if time is between start and end times
        try:
            file = open('auto.csv','r')
            auto = file.readline()
            file.close()
        except:
            pass

        if auto == '0':     # auto not set, continue
            s, u, w = read_control_values()
            try:
                file = open('%s/%s.csv' % (temp_data_dir, node_ID[0]),'w')
                file.write("i:%s,y:%s,u:0,w:%s" % (node_ID[0], str(setpoint), str(w)))
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

    elif (hr >= end_hour or hr < start_hour):      # check if time is between start and end times
        try:
            file = open('auto.csv','r')
            auto = file.readline()
            file.close()
        except:
            pass

        if auto == '1':     # auto not set, continue
            s, u, w = read_control_values()
            s = 0   # new setpoint is now 0
            try:
                file = open('%s/%s.csv' % (temp_data_dir, node_ID[0]),'w')
                file.write("i:%s,y:%s,u:0,w:%s" % (node_ID[0], str(s), str(w)))
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
            s, u, w = read_control_values()
            if u == '1':    # if there was manual override
                current_time = time.time()      # get current time
                last_override_time = os.path.getmtime('%s/%d.csv' % (temp_data_dir, int(node_ID[0])))      # get last date modified of node
                if current_time - last_override_time >= int(enforced_schedule_override_time)*60:     # check if x seconds have passed
                    s = 0   # new setpoint is now 0
                    try:
                        file = open('%s/%s.csv' % (temp_data_dir, node_ID[0]),'w')
                        file.write("i:%s,y:%s,u:0,w:%s" % (node_ID[0], str(s), str(w)))
                        file.close()
                    except:
                        pass
                else:
                    pass

    time.sleep(60) # check every min
