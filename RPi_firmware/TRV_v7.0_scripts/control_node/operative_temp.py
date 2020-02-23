# -*- coding: utf-8 -*-

# This script calculates the operative temperature based on 
# globe temperature and mean radiant temperature

# Developed by Akram Ali
# Last updated on: 02/23/2020

import os
import time
import json

time.sleep(10)
Tmr = 22    # initialize with some default values
To = 22

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


# get latest temperature from file
def read_temp(temp_type):
    if temp_type == 'air_temp':
        n = 1
    elif temp_type == 'globe_temp':
        n = 7
    try:
        file = open('%s/%d.csv' % (temp_data_dir, int(node_ID[0])+n),'r')        # get data from TRH node file
        data = file.readline()
        file.close()
    except:
        return 0
    parsed_data = {}
    try:
        for p in data.strip().split(","): #strip() removes trailing \n
            k,v = p.split(":")
            parsed_data[k] = v if v else 0.00
        if temp_type == 'air_temp':
            temperature = parsed_data.get('t')
            return temperature
        elif temp_type == 'globe_temp':
            globe_temp = parsed_data.get('a')
            return globe_temp
        
        # temperature_f = float(temperature)
        # temperature_f *= 1.8
        # temperature_f += 32     # convert to Fahrenheit
        # return temperature_f
    except:
        return 0


# save pid components to file to tune it later
def save_temp(Tmr, To):
    try:
        file = open('%s/%d_operative.csv' % (temp_data_dir, int(node_ID[0])+1),'w')
        file.write("i:%d,tmr:%3.3f,t:%3.3f" % (int(node_ID[0])+1, Tmr, To))   # t is operative temp in this file
        file.close()
    except:
        pass



# loop forever
while True:
    # check config
    config = load_config()

    # check if air temp or operative temp is selected
    if config[0]['acf']['temp_type'] == 'air_temp':
        pass
    elif config[0]['acf']['temp_type'] == 'operative_temp':
        Ta = float(read_temp('air_temp'))
        Tg = float(read_temp('globe_temp'))

        Va = 0.01   # in m/s - assuming very low velocity indoors
        e = 0.95    # emissivity of black globe
        D = 0.04    # diameter of ping pong ball in meters (40mm)

        # calculate mean radiant temperature
        Tmr = (((Tg+273.15)**4 + ((1.06 * 10**8 * Va**0.6)/(e * D**0.4)) * (Tg - Ta))**0.25) - 273.15
        
        # calculate operative temperature
        To = (Tmr + Ta) / 2

        save_temp(Tmr, To)
    
    time.sleep(30)