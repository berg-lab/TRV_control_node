# -*- coding: utf-8 -*-

# This script enables a scheduled operation of control valve for preheating
# It checks time and changes the setpoint of control valve accordingly

# Developed by Akram Ali
# Last updated on: 02/17/2020

from datetime import datetime
import time
import json
import os

# set all temporary directories
temp_data_dir = '/home/pi/datalogger/temp_data'
control_node_id_dir = '/home/pi/control_node'
json_dir = '/home/pi/control_node/'

# get node ID
node_ID = [".".join(f.split(".")[:-1]) for f in os.listdir(control_node_id_dir) if f.endswith(".node")]

# global variables
preheat = 0
u = 0
s = 0

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
def read_PWM():
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
        w = parsed_data.get('w')
        return w
    except:
        pass



time.sleep(5)  # give enough time for all other scripts to come up before executing this one

# create preheat.csv file with preheat value initialized to 0
try:
    file = open('preheat.csv','w')
    file.write('0')     # write 1 to indicate schedule is enforced - valve open
    file.close()
except:
    pass

while True:
    # read latest config from file
    config = load_config()
    if config[0]['acf']['preheat'] is False:
        pass

    elif config[0]['acf']['preheat'] is True:
        preheat_start_time = config[0]['acf']['preheat_start_time']
        preheat_end_time = config[0]['acf']['preheat_end_time']

        start_hour = datetime.strptime(preheat_start_time, '%H:%M').hour
        end_hour = datetime.strptime(preheat_end_time, '%H:%M').hour

        now = datetime.now()   # get current date/time
        hr = now.hour       # get current hour
        min = now.min
        if (start_hour <= hr < end_hour):     # check if time is between start and end time in config file
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
                pass    # don't do anything

            else:
                try:
                    file = open('preheat.csv','r')
                    preheat = file.readline()
                    file.close()

                except:
                    pass
                if preheat == '0':     # preheat not set, continue
                    if config[0]['acf']['control_strategy'] == 'motion':
                        s = config[0]['acf']['preheat_setpoint']
                    elif config[0]['acf']['control_strategy'] == 'pid_temp_motion':
                        s = config[0]['acf']['preheat_temp_setpoint']
                    w = read_PWM()
                    try:
                        file = open('%s/%s.csv' % (temp_data_dir, node_ID[0]),'w')
                        file.write("i:%s,y:%s,u:0,w:%s" % (node_ID[0], str(s), str(w)))
                        file.close()
                    except:
                        pass
                    try:
                        file = open('preheat.csv','w')
                        file.write('1')     # write 1 to indicate preheating is enforced - valve open
                        file.close()
                    except:
                        pass
                elif preheat == '1':
                    pass

        elif (hr >= end_hour or hr < start_hour):      # check if time is between start and end time in config file
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
                w = parsed_data.get('w')        # get PWM value
            except:
                pass

            if u == '1':    # if there was manual override
                pass    # don't do anything

            else:
                try:
                    file = open('preheat.csv','r')
                    preheat = file.readline()
                    file.close()
                except:
                    pass

                if preheat == '1':     # preheat set, continue
                    if config[0]['acf']['control_strategy'] == 'motion':
                        s = 0
                    elif config[0]['acf']['control_strategy'] == 'pid_temp_motion':
                        s = config[0]['acf']['check_motion_off_temp']

                    try:
                        file = open('%s/%s.csv' % (temp_data_dir, node_ID[0]),'w')
                        file.write("i:%s,y:%s,u:0,w:%s" % (node_ID[0], str(s), str(w)))
                        file.close()
                    except:
                        pass
                    try:
                        file = open('preheat.csv','w')
                        file.write('0')     # write 0 to indicate preheating is enforced - valve closed
                        file.close()
                    except:
                        pass

                elif preheat == '0':
                    pass    # don't do anything

    time.sleep(60) # check every min