# -*- coding: utf-8 -*-

# This script constantly sends data over serial at a defined interval

# Developed by Akram Ali
# Last updated on: 12/13/2019

import time
import serial
import os

# Parse data string
def parse(data):
    parsed_data = {}
    try:
        for p in data.strip().split(","): #strip() removes trailing \n
            k,v = p.split(":")
            parsed_data[k] = v if v else 0.00
        return parsed_data
    except:
        return 0

# temp = 0.0
# flag = 0
# id = 0
y = 0
u = 0
w = 0
temp_data_dir = '/home/pi/datalogger/temp_data'
control_node_id_dir = '/home/pi/control_node'

time.sleep(5)

try:
    # serialport = serial.Serial('/dev/ttyUSB0', 115200, timeout=1) # make sure baud rate is the same
    serialport = serial.Serial('/dev/ttyAMA0', 115200, timeout=1) # GPIO serial pins
    flag = 1
except serial.SerialException:
    #print('Serial Port Failed.')
    while True:     # loop forever
        pass

if flag == 1:
    serialport.flushInput() # clear input serial buffer
    serialport.flushOutput() # clear output serial buffer
    old_time = time.time()  # get time before starting while loop
    while True:     # keep reading serial port forever
        current_time = time.time()      # keep track of time
        if current_time - old_time >= 30:        # if ~30 seconds have passed, send data over serial
            old_time = time.time()

            # temp_data = [".".join(f.split(".")[:-1]) for f in os.listdir(temp_data_dir)]    # list of all temp data files
            node_ID = [".".join(f.split(".")[:-1]) for f in os.listdir(control_node_id_dir) if f.endswith(".node")]    # get node ID

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
            except:
                pass
            y = parsed_data.get('y')
            u = parsed_data.get('u')
            w = parsed_data.get('w')

            dataline = "<" + str(y) + "," + str(u) + "," + str(w) + ">"
            try:
                #serialport.write(data)  # send setpoint data over serial
                serialport.write(dataline)  # send data over serial
                time.sleep(5)
            except:
                pass

        time.sleep(0.1)    # wait a bit so CPU doesn't choke to def