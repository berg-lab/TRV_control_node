# -*- coding: utf-8 -*-

# This script sets (via PWM) a 270° servo (LD-27MG/DS3218MG) attached to a
# Honeywell thermostatic radiator valve control unit T100B1035/T104B1038

# Developed by Akram Ali
# Last updated on: 02/17/2019

import Adafruit_PCA9685
import time
import json
import os

time.sleep(5)

pwm = Adafruit_PCA9685.PCA9685()        # create Adafruit library object
pwm.set_pwm_freq(60)        # Set frequency to 60hz, good for servos.
s_start = 635   # initialize servo PWM ranges as normal (130-600 is for special servo)
s_end = 150
setpoint = 0
pwm_value = 400

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


# read setpoint from file
def get_setpoint(datatype):
    if datatype == 'latest':
        filename = node_ID[0]
    elif datatype == 'old':
        filename = str(node_ID[0]) + '_old'

    try:
        file = open('%s/%s.csv' % (temp_data_dir, filename),'r')
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
        return s
    except:
        return 0


# save setpoint to file
def save_setpoint(datatype, setpoint, pwm_value):
    if datatype == 'latest':
        filename = node_ID[0]
    elif datatype == 'old':
        filename = str(node_ID[0]) + '_old'
    
    try:
        file = open('%s/%s.csv' % (temp_data_dir, filename),'w')
        file.write("i:%s,y:%s,u:0,w:%s" % (node_ID[0], str(setpoint), str(pwm_value)))
        file.close()
    except:
        pass


# create old & current setpoint initially
save_setpoint('old', setpoint, pwm_value)
save_setpoint('latest', setpoint, pwm_value)

time.sleep(2)      # sleep a bit initially till all files are loaded

# loop forever
while True:
    # read latest config from file
    config = load_config()
    if config[0]['acf']['servo_type'] == 'normal':
        s_start = 635
        s_end = 150
    elif config[0]['acf']['servo_type'] == 'special_servo':
        s_start = 600
        s_end = 130

    setpoint_step_size = int(config[0]['acf']['setpoint_step_size'])

    # create list with PWM values
    pwm_list=[]
    step = int(round(s_start-s_end)/int(setpoint_step_size-1))     # step size
    for n in range(int(setpoint_step_size)):
        value = s_start - (step*n)  # increment steps 
        if abs(value-s_end) <= 3:   # i.e., if value is close to end value
            pwm_list.append(s_end)
        else:
            pwm_list.append(value)

    # get latest setpoint from file
    setpoint = get_setpoint('latest')
    
    # get old setpoint
    old_setpoint = get_setpoint('old')

    # set PWM only if setpoint is different from previous setpoint
    if old_setpoint != setpoint:
        pwm_value = pwm_list[int(setpoint)]
        # set servo PWM based on setpoint from file
        pwm.set_pwm(0, 0, pwm_value)  # use PWM value from list
        time.sleep(1.5)   # give some time for servo to move
        old_setpoint = setpoint     # overwrite old setpoint with new value

        save_setpoint('old', setpoint, pwm_value)

    time.sleep(5)      # sleep 5 secs to let other stuff run in bg