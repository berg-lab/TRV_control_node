# -*- coding: utf-8 -*-

# Control Node
# Developed by Akram Ali & Chris Riley
# Last updated on: 11/5/2018

version = "v0.5.1"

import RPi.GPIO as GPIO
import time
from time import sleep
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import os

temp_data_dir = '/home/pi/datalogger/temp_data'
control_node_id_dir = '/home/pi/control_node'
time.sleep(1)

# get latest temperature from file
def readTemp():
    # temp_data = [".".join(f.split(".")[:-1]) for f in os.listdir(temp_data_dir)]    # list of all temp data files
    node_ID = [".".join(f.split(".")[:-1]) for f in os.listdir(control_node_id_dir) if f.endswith(".node")]    # get node ID

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
    except:
        return 0


# get setpoint from file
def readSetpoint():
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
        s = parsed_data.get('y')
        setpoint_display(int(s))
        return int(s)
    except:
        return 0


# set new setpoint in file
def saveSetpoint(_s):
    # temp_data = [".".join(f.split(".")[:-1]) for f in os.listdir(temp_data_dir)]    # list of all temp data files
    node_ID = [".".join(f.split(".")[:-1]) for f in os.listdir(control_node_id_dir) if f.endswith(".node")]    # get node ID

    try:
        file = open('%s/%s.csv' % (temp_data_dir, node_ID[0]),'w')        # save data in file
        file.write("i:%s,y:%s,u:1" % (node_ID[0], str(_s)))
        file.close()
    except:
        pass


# display "min" or "max" on screen
def setpoint_display(s):
    global displayed_s
    displayed_s = str(s)
    if s == 0:
        displayed_s = "MIN"
    elif s == 6:
        displayed_s = "MAX"
    elif s < 0 or s > 6:
        displayed_s = "NAN"

# initialize global variables
temp = 0.0
s = 0
degree = u"\u00b0"      # degree symbol
displayed_s = "MIN"        # set point displayed on screen

# Raspberry Pi pin configuration:
#RST = None
RST = 24
button2 = 5 # replace button1 with button 2 when screen is flipped
button1 = 6
GPIO.setmode(GPIO.BCM)  # use GPIO number instread of board number
GPIO.setup(button1,GPIO.IN, pull_up_down=GPIO.PUD_UP)   # set up pullups for buttons
GPIO.setup(button2,GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Initialize OLED display
# disp = Adafruit_SSD1306.SSD1306_128_64(rst=RST) # create oled object
disp = Adafruit_SSD1306.SSD1306_128_32(rst=RST) # create oled object (128x32 OLED)
disp.begin()
disp.clear()
disp.display()
time.sleep(.1)

# Create blank image for drawing.
width = disp.width
height = disp.height
image = Image.new('1', (width, height)) # Make sure to create image with mode '1' for 1-bit color.
draw = ImageDraw.Draw(image)
draw.rectangle((0,0,width,height), outline=0, fill=0)   # Draw a black filled box to clear the image.

# Define some constants to allow easy resizing of shapes.
padding = -2
top = padding
bottom = height-padding
x = 0       # Move left to right keeping track of the current x position for drawing shapes.

# start message
draw.rectangle((0,0,width,height), outline=0, fill=0)   # Draw a black filled box to clear the image.
font = ImageFont.truetype('OpenSans-Bold.ttf', 17)  # font size is 19
draw.text((x, top),"Control Node",font=font, fill=255)
font = ImageFont.truetype('OpenSans-Regular.ttf', 12)
draw.text((x, top+20),"%s" % version,font=font, fill=255)
disp.image(image)   # Display image.
disp.display()
time.sleep(2)       # wait for a couple of secs

# Display initial values on screen
s = readSetpoint()
temp = readTemp()
draw.rectangle((0,0,width,height), outline=0, fill=0)   # clear image with black box
font = ImageFont.truetype('OpenSans-Bold.ttf', 17)       # font size is 19
draw.text((x, top),"Setpoint: " + displayed_s, font=font, fill=255)
font = ImageFont.truetype('OpenSans-Regular.ttf', 12)       # font size is 18
draw.text((x, top+20),"Room Temp: " + str(temp) + degree + "F",font=font, fill=255)
disp.image(image)   # Display image.
disp.display()
time.sleep(0.2)

old_time = time.time()  # get time before starting while loop
temp = readTemp()

# loop forever
while True:
    # keep track of time
    current_time = time.time()
    if current_time - old_time >= 30:        # if 30 seconds have passed, update temperature on screen
        old_time = time.time()
        temp = readTemp()
        s = readSetpoint()
        draw.rectangle((0,0,width,height), outline=0, fill=0)   # Draw a black filled box to clear the image.
        font = ImageFont.truetype('OpenSans-Bold.ttf', 17)       # font size is 19
        draw.text((x, top),"Setpoint: " + displayed_s, font=font, fill=255)
        font = ImageFont.truetype('OpenSans-Regular.ttf', 12)
        draw.text((x, top+20),"Room Temp: " + str(temp) + degree + "F",font=font, fill=255)
        disp.image(image)   # Display image.
        disp.display()
        time.sleep(0.2)
    else:
        pass

     # check if button 1 was pressed
    if GPIO.input(button1) == 0 and GPIO.input(button2) != 0:
        s -= 1
        if s <= 0:
            s = 0
            displayed_s = "MIN"
        else:
            displayed_s = str(s)
        saveSetpoint(s)
        # readTemp()
        draw.rectangle((0,0,width,height), outline=0, fill=0)   # Draw a black filled box to clear the image.
        font = ImageFont.truetype('OpenSans-Bold.ttf', 17)       # font size is 19
        draw.text((x, top),"Setpoint: " + displayed_s, font=font, fill=255)
        font = ImageFont.truetype('OpenSans-Regular.ttf', 12)
        draw.text((x, top+20),"Room Temp: " + str(temp) + degree + "F",font=font, fill=255)
        disp.image(image)   # Display image.
        disp.display()
        time.sleep(0.1)

    # check if button 2 was pressed
    if GPIO.input(button2) == 0 and GPIO.input(button1) != 0:
        s += 1
        if s >= 6:
            s = 6
            displayed_s = "MAX"
        else:
            displayed_s = str(s)
        saveSetpoint(s)
        # readTemp()
        draw.rectangle((0,0,width,height), outline=0, fill=0)   # Draw a black filled box to clear the image.
        font = ImageFont.truetype('OpenSans-Bold.ttf', 17)       # font size is 19
        draw.text((x, top),"Setpoint: " + displayed_s, font=font, fill=255)
        font = ImageFont.truetype('OpenSans-Regular.ttf', 12)
        draw.text((x, top+20),"Room Temp: " + str(temp) + degree + "F",font=font, fill=255)
        disp.image(image)   # Display image.
        disp.display()
        time.sleep(0.1)

    # if both buttons are pressed, do nothing
    if GPIO.input(button1) == 0 and GPIO.input(button2) == 0:
        pass
    # sleep the code a bit so CPU doesn't choke to death with 100% usage
    time.sleep(0.005)
