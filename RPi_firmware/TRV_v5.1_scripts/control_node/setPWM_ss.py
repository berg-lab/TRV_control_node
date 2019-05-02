# -*- coding: utf-8 -*-

# This script sets (via PWM) a 270° servo (LD-27MG/DS3218MG) attached to a
# Honeywell thermostatic radiator valve control unit T100B1035/T104B1038

# Developed by Akram Ali
# Last updated on: 1/17/2019

import time
import Adafruit_PCA9685
import os

time.sleep(5)

pwm = Adafruit_PCA9685.PCA9685()        # create Adafruit library object
pwm.set_pwm_freq(60)        # Set frequency to 60hz, good for servos.
temp_data_dir = '/home/pi/datalogger/temp_data'
control_node_id_dir = '/home/pi/control_node'

# create old & current setpoint initially
try:
    file = open('_s.csv','w')
    file.write(int('0'))
    file.close()
except:
    pass

node_ID = [".".join(f.split(".")[:-1]) for f in os.listdir(control_node_id_dir) if f.endswith(".node")]    # get node ID

try:
    file = open('%s/%s.csv' % (temp_data_dir, node_ID[0]),'w')
    file.write("i:%s,y:0,u:0" % node_ID[0])
    file.close()
except:
    pass

while True:
    time.sleep(5)      # sleep 10 secs to let other stuff run in bg

    # read setpoint files
    # temp_data = [".".join(f.split(".")[:-1]) for f in os.listdir(temp_data_dir)]    # list of all temp data files
    node_ID = [".".join(f.split(".")[:-1]) for f in os.listdir(control_node_id_dir) if f.endswith(".node")]    # get node ID

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

        sp = 0      # initialize pwm value

        if s == '0':
            sp = 600
        elif s == '1':
            sp = 520
        elif s == '2':
            sp = 442
        elif s == '3':
            sp = 364
        elif s == '4':
            sp = 286
        elif s == '5':
            sp = 208
        elif s == '6':
            sp = 130
        else:
            sp = 600

        # set servo PWM based on setpoint
        pwm.set_pwm(0, 0, sp)
        time.sleep(1.5)   # give some time for servo to move
        old_s = s     # overwrite old setpoint with new value
        try:
            file = open('_s.csv','w')
            file.write(str(old_s))
            file.close()
        except:
            pass
