# -*- coding: utf-8 -*-

# Control Node
# Developed by Akram Ali & Chris Riley
# Last updated on: 12/18/2019

version = "v6.0"

import Adafruit_GPIO.SPI as SPI
from datetime import datetime
import RPi.GPIO as GPIO
import Adafruit_SSD1306
import Adafruit_SSD1306_orig
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import subprocess
import shlex
import time
import json
import os

# set all temporary directories
temp_data_dir = '/home/pi/datalogger/temp_data'
control_node_id_dir = '/home/pi/control_node'
json_dir = '/home/pi/control_node/'

# get node ID
node_ID = [".".join(f.split(".")[:-1]) for f in os.listdir(control_node_id_dir) if f.endswith(".node")]

# set all scripts to check if they're running
scripts = ['config','read_GPIO', 'read_serial', 'write_serial','set_PWM','datalogger',
'monitor_core_temp','preheat','enforce_schedule','check_motion','pid_temp']

# initialize global variables
temp = 0.0
s = 0
num_setpoint = 0   # initial setpoint
temp_setpoint = 72  # initial setpoint
button1 = 5
button2 = 6

RST = 24
disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST)
screen_rotation = 'normal'
top_text = ''
bottom_text = ''
top_font_size = 17
bottom_font_size = 12

time.sleep(1)

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

# get current running scripts
def get_running_scripts():
    PIDs=[]
    script_status=[]
    ss = ''
    for s in scripts:
        cmd = "pgrep -f 'python %s.py'" % s
        try:
            output = subprocess.check_output(shlex.split(cmd), shell=False).decode("utf-8")
        except subprocess.CalledProcessError:
            output = ''
        PIDs.append(output)
        time.sleep(0.01)
    n=0

    for p in PIDs:
        n+=1
        if n == 6 or n == 8:
            script_status.append(' ')
        if p == '':
            script_status.append('0')
        else:
            script_status.append('1')
    ss = ''.join(script_status)
    return ss

# get latest temperature from file
def read_temp():
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
        return round(temperature_f, 2)
    except:
        return 0


# get setpoint from file
def read_setpoint():
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
        s = parsed_data.get('y')
        setpoint_display(int(s))
        return int(s)
    except:
        return 0

# set new setpoint in file
def save_setpoint(_s):
    try:
        file = open('%s/%s.csv' % (temp_data_dir, node_ID[0]),'w')        # save data in file
        file.write("i:%s,y:%s,u:1,w:0" % (node_ID[0], str(_s)))
        file.close()
    except:
        pass


# display "min" or "max" on screen
def setpoint_display(_s):
    global displayed_s
    global num_setpoint
    global temp_setpoint

    degree = u"\u00b0"      # degree symbol

    if config[0]['acf']['control_strategy'] == 'pid_temp' or config[0]['acf']['control_strategy'] == 'pid_temp_motion':
        displayed_s = str(int(_s)) + degree + "F"  # add degree symbol
        if _s <= 60:
            displayed_s = "MIN"
            temp_setpoint = 60
        elif _s >= 90:
            displayed_s = "MAX"
            temp_setpoint = 90
        elif 60 < _s < 90:
            temp_setpoint = _s

    else:
        displayed_s = str(_s)
        if _s <= 0:
            displayed_s = "MIN"
            num_setpoint = 0
        elif _s >= 6:
            displayed_s = "MAX"
            num_setpoint = 6
        elif 0 < _s < 6:
            num_setpoint = _s


def check_screen_rotation():
    global button1
    global button2
    global top_text
    global bottom_text
    global top_font_size
    global bottom_font_size
    global disp
    global config
    global screen_rotation
    global RST

    if screen_rotation != config[0]['acf']['screen_rotation']:  # if there is new screen rotation in cnpofig file
        screen_rotation = config[0]['acf']['screen_rotation']
        if config[0]['acf']['screen_rotation'] == 'normal':
            button1 = 5
            button2 = 6
            disp = Adafruit_SSD1306_orig.SSD1306_128_32(rst=RST) # create oled object (128x32 OLED) - original library
            disp.begin()
            disp.clear()
            disp.display()
            time.sleep(.1)
        elif config[0]['acf']['screen_rotation'] == 'flipped':
            disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST) # create oled object (128x32 OLED) - flipped library
            disp.begin()
            disp.clear()
            disp.display()
            time.sleep(.1)
            button2 = 5
            button1 = 6


def config_display_text():
    global top_text
    global bottom_text
    global top_font_size
    global bottom_font_size
    global config

    if config[0]['acf']['control_strategy'] == 'pid_temp' or config[0]['acf']['control_strategy'] == 'pid_temp_motion':
        top_text = 'Set Temp: '
        bottom_text = 'Room Temp: '
        top_font_size = 17
        bottom_font_size = 12
    else:
        top_text = 'Setpoint: '
        bottom_text = 'Room Temp: '
        top_font_size = 17
        bottom_font_size = 12


def update_screen(setpoint, roomtemp):
    global top_text
    global bottom_text
    global top_font_size
    global bottom_font_size
    global disp
    global config
    global displayed_s

    degree = u"\u00b0"      # degree symbol

    # Create blank image for drawing.
    width = disp.width
    height = disp.height
    image = Image.new('1', (width, height)) # Make sure to create image with mode '1' for 1-bit color.
    draw = ImageDraw.Draw(image)

    # Define some constants to allow easy resizing of shapes.
    padding = -2
    top = padding
    #bottom = height-padding
    x = 0       # Move left to right keeping track of the current x position for drawing shapes.

    # display message
    draw.rectangle((0,0,width,height), outline=0, fill=0)   # clear image with black box
    top_font = ImageFont.truetype('OpenSans-Bold.ttf', top_font_size)       # default top font size is 17
    bottom_font = ImageFont.truetype('OpenSans-Regular.ttf', bottom_font_size)       # deafult bottom font size is 12

    if str(setpoint) == 'start': # initial start message has empty string
        top_text = 'Control Node'
        bottom_text = str(version)
        draw.text((x, top),top_text, font=top_font, fill=255)
        draw.text((x, top+20),bottom_text, font=bottom_font, fill=255)
        disp.image(image)   # Display image.
        disp.display()
        time.sleep(2)

    elif str(setpoint) == 'debug':
        # debug stuff
        IP = subprocess.check_output("hostname -I", shell=True).decode("utf-8")
        cmd = "df -h | awk '$NF==\"/\"{printf \"Disk: %d/%d GB  %s\", $3,$2,$5}'"
        Disk = subprocess.check_output(cmd, shell=True).decode("utf-8")
        script = get_running_scripts()
        dt = datetime.now().strftime('%Y/%m/%d %H:%M:%S')

        # draw.rectangle((0,0,width,height), outline=0, fill=0)   # Draw a black filled box to clear the image.
        font = ImageFont.load_default()
        draw.text((x, top+0),"IP: " + IP, font=font, fill=255)
        draw.text((x, top+8), Disk, font=font, fill=255)
        draw.text((x, top+16), "PY: " + script, font=font, fill=255)
        draw.text((x, top+25), dt, font=font, fill=255)

        disp.image(image)   # Display image.
        disp.display()
        time.sleep(5)

    else:
        # draw.rectangle((0,0,width,height), outline=0, fill=0)   # Draw a black filled box to clear the image.
        draw.text((x, top),top_text + displayed_s, font=top_font, fill=255)
        draw.text((x, top+20),bottom_text + str(roomtemp) + degree + "F",font=bottom_font, fill=255)
        disp.image(image)   # Display image.
        disp.display()
        time.sleep(0.1)
    

# Raspberry Pi pin configuration:
# RST = 24
# button2 = 5 # replace button1 with button 2 when screen is flipped
# button1 = 6
GPIO.setmode(GPIO.BCM)  # use GPIO number instread of board number
GPIO.setup(button1,GPIO.IN, pull_up_down=GPIO.PUD_UP)   # set up pullups for buttons
GPIO.setup(button2,GPIO.IN, pull_up_down=GPIO.PUD_UP)

# start script
config = load_config()
check_screen_rotation()
update_screen('start','')      # Display start message on screen
config_display_text()

# display initial values on screen
if config[0]['acf']['control_strategy'] == 'pid_temp' or config[0]['acf']['control_strategy'] == 'pid_temp_motion':
    s = temp_setpoint
    save_setpoint(temp_setpoint)
else:
    s = num_setpoint
    # save_setpoint(num_setpoint)
setpoint_display(s)
temp = read_temp()
update_screen(s, temp)      

old_time_30 = time.time()  # keep track of 30 second timer
old_time_5 = time.time()    # keep track of 5 second timer

# loop forever
while True:
    # keep track of time
    current_time = time.time()

    # read latest config from file after 5 seconds
    if current_time - old_time_5 >= 5:
        old_time_5 = time.time()
        config = load_config()
        check_screen_rotation()
        # config_display_text()

    # if 30 seconds have passed, update room temperature on screen
    if current_time - old_time_30 >= 30:
        old_time_30 = time.time()
        s = read_setpoint()
        temp = read_temp()
        setpoint_display(s)
        update_screen(s, temp)
        # save_setpoint(temp_setpoint)
    else:
        pass

    # check if button 1 was pressed
    if GPIO.input(button1) == 0 and GPIO.input(button2) != 0:
        if config[0]['acf']['control_strategy'] == 'pid_temp' or config[0]['acf']['control_strategy'] == 'pid_temp_motion':
            temp_setpoint -= 1
            setpoint_display(temp_setpoint)
            save_setpoint(temp_setpoint)
        else:
            num_setpoint -= 1
            setpoint_display(num_setpoint)
            save_setpoint(num_setpoint)
        
        s = read_setpoint()
        temp = read_temp()
        update_screen(s, temp)

    # check if button 2 was pressed
    if GPIO.input(button2) == 0 and GPIO.input(button1) != 0:
        if config[0]['acf']['control_strategy'] == 'pid_temp' or config[0]['acf']['control_strategy'] == 'pid_temp_motion':
            temp_setpoint += 1
            setpoint_display(temp_setpoint)
            save_setpoint(temp_setpoint)
        else:
            num_setpoint += 1
            setpoint_display(num_setpoint)
            save_setpoint(num_setpoint)

        s = read_setpoint()
        temp = read_temp()
        update_screen(s, temp)

    # if both buttons are pressed, do nothing
    if GPIO.input(button1) == 0 and GPIO.input(button2) == 0:
        start_time = time.time()
        while GPIO.input(button1) == 0 and GPIO.input(button2) == 0:
            elapsed_time = time.time() - start_time
            if elapsed_time >= 3 and elapsed_time <= 3.5:
                update_screen('debug','')
                break
            elif elapsed_time >= 7:
                break
            else:
                time.sleep(0.005)
            

    # sleep the code a bit so CPU doesn't choke to death with 100% usage
    time.sleep(0.005)
