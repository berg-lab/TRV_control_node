# -*- coding: utf-8 -*-

# This script sets (via PWM) a 270° servo (LD-27MG/DS3218MG) attached to a
# Honeywell thermostatic radiator valve control unit T100B1035/T104B1038

# Developed by Akram Ali
# Last updated on: 12/16/2019

import Adafruit_PCA9685
import time
import json
import os

time.sleep(5)

pwm = Adafruit_PCA9685.PCA9685()        # create Adafruit library object
pwm.set_pwm_freq(60)        # Set frequency to 60hz, good for servos.
s_start = 635   # initialize servo PWM ranges as normal (130-600 is for special servo)
s_end = 150

# set all temporary directories
temp_data_dir = '/home/pi/datalogger/temp_data'
control_node_id_dir = '/home/pi/control_node'
json_dir = '/home/pi/control_node/'

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

# get node ID
node_ID = [".".join(f.split(".")[:-1]) for f in os.listdir(control_node_id_dir) if f.endswith(".node")]

# create old & current setpoint initially
try:
    file = open('_s.csv','w')
    file.write(int('0'))
    file.close()
except:
    pass

try:
    file = open('%s/%s.csv' % (temp_data_dir, node_ID[0]),'w')
    file.write("i:%s,y:0,u:0" % node_ID[0])
    file.close()
except:
    pass

while True:
    time.sleep(5)      # sleep 5 secs to let other stuff run in bg

    # read latest config from file
    config = load_config()
    if config[0]['acf']['servo_type'] == 'normal':
        s_start = 635
        s_end = 150
    elif config[0]['acf']['servo_type'] == 'special_servo':
        s_start = 600
        s_end = 130

    # create list with PWM values
    pwm_list=[]
    step = int(round(s_start-s_end)/6)     # step size
    for n in range(7):
        value = s_start - (step*n)  # increment steps 
        if abs(value-s_end) <= 3:   # i.e., if value is close to end value
            pwm_list.append(s_end)
        else:
            pwm_list.append(value)

    try:
        file = open('%s/%s.csv' % (temp_data_dir, node_ID[0]),'r')        # get data from file
        data = file.readline()
        file.close()
    except:
        pass
    parsed_data = {}
    try:
        for p in data.strip().split(","): #strip() removes trailing \n
            k,v = p.split(":")
            parsed_data[k] = v if v else 0.00
        s = parsed_data.get('y')
    except:
        pass

    try:
        file = open('_s.csv','r')
        old_s = file.readline().rstrip('\n') # remove trailing newline
        file.close()
    except:
        pass

    # set PWM only if setpoint is different from previous setpoint
    if old_s != s:
        # set servo PWM based on setpoint from file
        pwm.set_pwm(0, 0, pwm_list[int(s)])  # use PWM value from list
        time.sleep(1.5)   # give some time for servo to move
        old_s = s     # overwrite old setpoint with new value
        try:
            file = open('_s.csv','w')
            file.write(str(old_s))
            file.close()
        except:
            pass
