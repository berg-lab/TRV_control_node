# -*- coding: utf-8 -*-

# This script constantly monitors incoming data over serial and saves it to a temp file

# Developed by Akram Ali
# Last updated on: 12/19/2019

import time
import serial

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

time.sleep(0.2)

id = 0
try:
    # serialport = serial.Serial('/dev/ttyUSB0', 115200, timeout=1) # make sure baud rate is the same
    serialport = serial.Serial('/dev/ttyAMA0', 115200, timeout=1) # GPIO serial pins
    flag = 1
except serial.SerialException:
    #print('Serial Port Failed.')
    while True:     # loop forever
        time.sleep(1)
        pass

if flag == 1:
    serialport.flushInput() #clear input serial buffer
    serialport.flushOutput() #clear output serial buffer
    while True:     # keep reading serial port forever
        data = serialport.read(1)
        n = serialport.in_waiting
        if n:    # wait till data arrives and then read it
            data = data + serialport.readline()    # read one line
            # print (data)
            if data[0]=='i':        # check for good data packets
                parsed_data = parse(data)   # parse data string into dictionary
                if parsed_data != 0:
                    i = parsed_data.get('i')    # get node ID
                    if i is not None:     # check if string is not 'NoneType'
                        id = int(i)     # type cast string to int
                        if id % 10 == 0:    # if serial print from node id (shouldn't be receiving this, only sending it)
                            pass
                        else:
                            try:
                                file = open('/home/pi/datalogger/temp_data/%d.csv' % id,'w')
                                file.write(data)     # save data in a csv file
                                file.close()
                            except:
                                pass
                else:
                    pass
            else:       # either incomplete packet received or bad data packet format received
                continue    # ignore bad packets

        time.sleep(0.01)    # wait a bit so CPU doesn't choke to def
