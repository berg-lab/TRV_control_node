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

        #
        # data = serialport.read(1)
        # n = serialport.in_waiting
        # if n:    # wait till data arrives and then read it
        #     data = data + serialport.readline()    # read one line
        #     #data = data + serialport.read(n)
        #     #print (data)
        #     if data[0]=='i':        # check for good data packets
        #         parsed_data = parse(data)   # parse data string into dictionary
        #         if parsed_data != 0:
        #             i = parsed_data.get('i')    # get node ID
        #             if i is not None:     # check if string is not 'NoneType'
        #                 id = int(i)     # type cast string to int
        #
        #             if (id - 1) % 10 == 0:        # check if data is from T/RH/L node (ids: 11,21,31,41,etc.)
        #                 temperature = parsed_data.get('t')    # get temperature in celsius
        #                 temperature_f = float(temperature)
        #                 temperature_f *= 1.8
        #                 temperature_f += 32     # convert to Fahrenheit
        #                 try:
        #                     file = open('t.csv','w')
        #                     file.write(str(temperature_f))     # save temperature in a csv file
        #                     file.close()
        #                 except:
        #                     pass
        #
        #             elif (id - 2) % 10 == 0:        # check for data from motion node
        #                 motion = parsed_data.get('m')    # get motion status
        #                 try:
        #                     file = open('m.csv','w')
        #                     file.write(str(motion))     # save motion status in a csv file
        #                     file.close()
        #                 except:
        #                     pass
        #
        #     else:       # either incomplete packet received or bad data packet format received
        #         continue    # ignore bad packets
