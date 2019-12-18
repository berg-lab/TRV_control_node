# -*- coding: utf-8 -*-

# This script runs a PID control to reach a desired set temperature
# The output is servo setpoint values

# Developed by Akram Ali
# Last updated on: 11/27/2019

from simple_pid import PID
import time
import os
from pathlib import Path
import Adafruit_PCA9685

pwm = Adafruit_PCA9685.PCA9685()        # create Adafruit library object
pwm.set_pwm_freq(60)        # Set frequency to 60hz, good for servos.

pid = PID(1, 0.1, 0.05)
sp = 400    # starting setpoint
setpoint = 75 # starting set temperature

pid.sample_time = 60  # update every 60 seconds
pid.output_limits = (-200, 200)    # output value will be between -200 and 200

temp_data_dir = '/home/pi/datalogger/temp_data'
control_node_id_dir = '/home/pi/control_node'

node_ID = [".".join(f.split(".")[:-1]) for f in os.listdir(control_node_id_dir) if f.endswith(".node")]    # get node ID

# get latest setpoint from file
def readSetpoint():
    global setpoint
    try:
        file = open('%s/st.csv' % control_node_id_dir,'r')
        setpoint = float(file.readline().rstrip('\n')) # remove trailing newline
        file.close()
    except:
        pass


# get latest temperature from file
def readTemp():
    try:
        file = open('%s/%d.csv' % (temp_data_dir, int(node_ID[0])+1),'r')        # get data from TRH node file
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
        return temperature
    except:
        return 0


#set PWM output of the servo
def setNewPWM(output, current_temp):
    global sp
    global setpoint
    # output = round(output * 10) # make the output larger for quicker changes to the PID control
    # output = int(output)

    if current_temp - setpoint > 0:
        sp = sp + abs(output)
    elif current_temp - setpoint < 0:
        sp = sp - output

    if sp > 635:
        sp = 635
    elif sp < 150:
        sp = 150

    # set servo PWM based on setpoint
    pwm.set_pwm(0, 0, sp)

    print ("Current Temp: " + str(current_temp) + "     Setpoint: " + str(setpoint) + "     PID output: " + str(output) + "     PWM setpoint: " + str(sp))


while True:
    readSetpoint()  # get latest setpoint
    pid.setpoint = float(setpoint)     # assign new setpoint to PID function
    current_temp = readTemp()   # read current temperature
    output = pid(float(current_temp))   # feed current temperature into PID function and get output

    setNewPWM(int(output), float(current_temp))  # set servo based on PID output

    time.sleep(30)  # sleep so script doesn't bog down

