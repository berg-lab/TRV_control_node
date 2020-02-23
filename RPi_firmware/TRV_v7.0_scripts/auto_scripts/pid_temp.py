# -*- coding: utf-8 -*-

# This script runs a PID control to reach a desired set temperature
# The output is servo setpoint values

# Developed by Akram Ali
# Last updated on: 02/23/2020

from pathlib import Path
import Adafruit_PCA9685
from simple_pid import PID
from datetime import datetime
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

# initialize global objects and variables
pwm = Adafruit_PCA9685.PCA9685()        # create Adafruit library object
pwm.set_pwm_freq(60)        # Set frequency to 60hz, good for servos.

u = 0
pid_temp = 75
pid_temp_sleep_interval = 30    # default sleep interval for script
pid = PID(1, 0.1, 0.05)
sp = 400    # starting setpoint
setpoint = 75 # starting set temperature
pid.sample_time = 60  # update every 60 seconds
pid.output_limits = (-200, 200)    # output value will be between -200 and 200
pid_temp_offset = 0.1   # default offset

time.sleep(5)   # sleep a bit initially

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


# get latest setpoint from file
def read_setpoint():
    global setpoint
    global u
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
        setpoint = int(parsed_data.get('y'))
        u = parsed_data.get('u')
    except:
        pass


# get latest temperature from file
def read_temp():
    global config
    temp_type = config[0]['acf']['temp_type']
    if temp_type == 'air_temp':
        filename = ''
    elif temp_type == 'operative_temp':
        filename = '_operative'
    try:
        file = open('%s/%d.csv' % (temp_data_dir, int(node_ID[0])+1, filename),'r')        # get data from TRH node file
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
        return temperature_f
    except:
        return 0


#set PWM output of the servo
def set_new_PWM(output, current_temp):
    global sp
    global u
    global setpoint
    global config

    # output = round(output * 10) # make the output larger for quicker changes to the PID control
    # output = int(output)

    if current_temp - setpoint > 0:
        sp = sp + abs(output)
    elif current_temp - setpoint < 0:
        sp = sp - output

    if config[0]['acf']['servo_type'] == 'normal':
        s_start = 635
        s_end = 150
    elif config[0]['acf']['servo_type'] == 'special_servo':
        s_start = 600
        s_end = 130

    if sp > s_start:
        sp = s_start
    elif sp < s_end:
        sp = s_end

    # set servo PWM based on setpoint
    pwm.set_pwm(0, 0, sp)

    # save latest PWM value to temp file
    try:
        file = open('%s/%s.csv' % (temp_data_dir, node_ID[0]),'w')
        file.write("i:%s,y:%s,u:%s,w:%s" % (node_ID[0], str(setpoint), str(u), str(sp)))
        file.close()
    except:
        pass


# get latest parameters for the PID function from the config file
def update_PID_params():
    global pid_temp_sleep_interval
    global pid_temp_offset

    if config[0]['acf']['control_strategy'] == 'pid_temp' or config[0]['acf']['control_strategy'] == 'pid_temp_motion':
        kp = float(config[0]['acf']['proportional_gain'])
        ki = float(config[0]['acf']['integral_gain'])
        kd = float(config[0]['acf']['derivative_gain'])
        sample_time = int(config[0]['acf']['pid_sample_time'])
        pid_lower_limit = int(config[0]['acf']['pid_lower_limit'])
        pid_upper_limit = int(config[0]['acf']['pid_upper_limit'])
        pid_temp_offset = float(config[0]['acf']['pid_temp_offset'])
        pid_temp_sleep_interval = int(config[0]['acf']['pid_temp_sleep_interval'])

        pid.tunings = (kp, ki, kd)
        pid.sample_time = sample_time  # update every 60 seconds
        pid.output_limits = (pid_lower_limit, pid_upper_limit)    # output value will be between -200 and 200


# save pid components to file to tune it later
def save_pid_components(output):
    global sp

    p, i, d = pid.components  # the separate terms are now in p, i, d
    # dt = datetime.now().strftime('%Y/%m/%d %H:%M:%S')

    try:
        file = open('%s/%s_PID.csv' % (temp_data_dir, node_ID[0]),'w')
        file.write("i:%s,kp:%s,ki:%s,kd:%s,x:%s" % (node_ID[0], str(p), str(i), str(d), str(output)))
        file.close()
    except:
        pass


# loop forever
while True:
    config = load_config()
    update_PID_params()

    read_setpoint()  # get latest setpoint
    pid.setpoint = float(setpoint)     # assign new setpoint to PID function

    current_temp = read_temp()   # read current temperature

    # tune PID function to react faster
    if setpoint >= (current_temp + pid_temp_offset):
        pid_temp = current_temp + pid_temp_offset
    elif setpoint < (current_temp - pid_temp_offset):
        pid_temp = current_temp - pid_temp_offset

    output = pid(float(pid_temp))   # feed tuned temperature into PID function and get output
    set_new_PWM(int(output), float(current_temp))  # set servo based on PID output

    save_pid_components(output) # save pid components, output and PWM value to file

    time.sleep(pid_temp_sleep_interval)  # sleep so script doesn't bog down