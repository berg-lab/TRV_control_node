# -*- coding: utf-8 -*-

# This script checks the last state of motion detected
# and changes the setpoint of control valve accordingly
# It also allows for auto scripts to run uninterrupted

# Developed by Akram Ali
# Last updated on: 02/17/2020

import time
import os
import json

# set all temporary directories
temp_data_dir = '/home/pi/datalogger/temp_data'
control_node_id_dir = '/home/pi/control_node'
auto_scripts_dir = '/home/pi/auto_scripts'
json_dir = '/home/pi/control_node/'

# get node ID
node_ID = [".".join(f.split(".")[:-1]) for f in os.listdir(control_node_id_dir) if f.endswith(".node")]

# global default variables
check_motion_timeout = 1800     # default timeout is 30 mins
check_motion_setpoint = 4
check_motion_min_temp = 70
check_motion_temp_setpoint = 75
check_motion_value = 'custom'   # default
check_motion_previous_setpoint = 70

time.sleep(10)   # wait a bit so other scripts can start running first

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

# get latest motion status from file
def read_motion():
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
def read_control_node():
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
        

# get latest temperature reading from file
def read_temperature():
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
        temperature = parsed_data.get('t')
        temperature_f = float(temperature)
        temperature_f *= 1.8
        temperature_f += 32     # convert to Fahrenheit
        return round(temperature_f, 2)
    except:
        return 0


# get latest values from config file and update
def update_check_motion_params():
    global config
    global check_motion_timeout
    global check_motion_setpoint
    global check_motion_min_temp
    global check_motion_temp_setpoint
    global check_motion_off_temp
    global check_motion_value

    check_motion_value = config[0]['acf']['check_motion_value']

    check_motion_timeout = int(config[0]['acf']['check_motion_timeout'])*60     # timeout in seconds
    check_motion_min_temp = int(config[0]['acf']['check_motion_min_temp'])

    if config[0]['acf']['control_strategy'] == 'motion':
        check_motion_setpoint = int(config[0]['acf']['check_motion_setpoint'])
        
    elif config[0]['acf']['control_strategy'] == 'pid_temp_motion':
        if check_motion_value == 'custom':
            check_motion_setpoint = int(config[0]['acf']['check_motion_temp_setpoint'])
        elif check_motion_value == 'previous':
            check_motion_setpoint = check_motion_previous_setpoint

        check_motion_off_temp = int(config[0]['acf']['check_motion_off_temp'])


# write data to file
def write_file(command, data):
    global config

    if config[0]['acf']['control_strategy'] == 'pid_temp_motion':
        pwm = read_file('pwm')
    else:
        pwm = 0

    if command == 'save_setpoint':
        try:
            file = open('%s/%s.csv' % (temp_data_dir, node_ID[0]),'w')        # save data in file
            file.write("i:%s,y:%s,u:0,w:%s" % (node_ID[0], str(data), str(pwm)))
            file.close()
        except:
            pass


# read data from file
def read_file(command):
    if command == 'preheat':
        try:
            file = open('preheat.csv','r')
            pre = file.readline()
            file.close()
            return pre
        except:
            pass

    elif command == 'pwm':
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


# check motion forever
while True:
    # get latest config
    config = load_config()
    update_check_motion_params()
    
    # check if there was manual override
    preheat = read_file('preheat')

    # preheat not yet set, continue
    if preheat == '0':
        current_time = time.time()      # get current time
        try:
            last_motion_time = os.path.getmtime('%s/%d.csv' % (temp_data_dir, int(node_ID[0])+2))      # get last date modified of m.csv
        except:
            last_motion_time = 0

        elapsed_time = current_time - last_motion_time
        
        # read current motion state
        motion = read_motion()

        # if no motion detected
        if motion == '0':

            # check if 30 mins have passed
            if elapsed_time >= check_motion_timeout:
                s, u = read_control_node()
                if config[0]['acf']['control_strategy'] == 'check_motion':
                    if s == '0':
                        pass    # don't do anything if setpoint is already at 0
                    else:
                        check_motion_previous_setpoint = s  # save previous setpoint
                        check_motion_setpoint = 0       # turn off control
                        write_file('save_setpoint', check_motion_setpoint)
                
                elif config[0]['acf']['control_strategy'] == 'pid_temp_motion':
                    if int(s) <= check_motion_off_temp:
                        pass    # don't do anything if setpoint is already at lowest temp setting
                    else:
                        check_motion_setpoint = check_motion_off_temp
                        write_file('save_setpoint', check_motion_setpoint)

            else:
                pass
        
        # if motion detected
        elif motion == '1':
            s, u = read_control_node()
            if u == '1':    # if there was manual override
                pass    # don't do anything

            elif u == '0':   # no manual override yet
                temp = read_temperature()
                if temp <= check_motion_min_temp:
                    
                    update_check_motion_params()    # get default setpoint from config
                    if int(s) >= check_motion_setpoint:
                        pass
                    else:
                        if check_motion_value == 'custom':
                            write_file('save_setpoint', check_motion_setpoint)
                        elif check_motion_value == 'previous':
                            write_file('save_setpoint', check_motion_previous_setpoint)
            else:
                pass

    # preheat already set, pass
    elif preheat == '1':
        pass

    time.sleep(5) # check motion every 5 seconds