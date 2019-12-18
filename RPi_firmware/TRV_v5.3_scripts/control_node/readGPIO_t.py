# -*- coding: utf-8 -*-

# Control Node
# Developed by Akram Ali & Chris Riley
# Last updated on: 11/26/2019

version = "v0.5.3"

import RPi.GPIO as GPIO
import time
from time import sleep
from datetime import datetime
import Adafruit_GPIO.SPI as SPI
import Adafruit_SSD1306
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
import os
import subprocess
import shlex

temp_data_dir = '/home/pi/datalogger/temp_data'
control_node_id_dir = '/home/pi/control_node'
scripts = ['readGPIO', 'readSerial', 'writeSerial','setPWM','setPWM_ss','datalogger',
'monitor_core_temp','preheat','enforceSchedule','checkMotion','temp_PID']
time.sleep(1)
setpoint = 75   # initial setpoint
degree = u"\u00b0"      # degree symbol

# get current running scripts
def get_running_scripts():
    PIDs=[]
    script_status=[]
    ss = ''
    for s in scripts:
        cmd = "pgrep -f 'python %s.py'" % s
        try:
            output = subprocess.check_output(shlex.split(cmd), shell=False).decode("utf-8")
        except subprocess.CalledProcessError as e:
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


# get latest setpoint from file
def readSetpoint():
    global setpoint
    try:
        file = open('%s/st.csv' % control_node_id_dir,'r')
        setpoint = float(file.readline().rstrip('\n')) # rstrip('\n') removes trailing newline
        file.close()
    except:
        pass
    return setpoint


# set latest setpoint from file
def setSetpoint():
    global setpoint
    try:
        file = open('%s/st.csv' % control_node_id_dir,'w')
        file.write(str(setpoint))
        file.close()
    except:
        pass


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


# set new setpoint in file
def saveSetpoint():
    global setpoint
    # temp_data = [".".join(f.split(".")[:-1]) for f in os.listdir(temp_data_dir)]    # list of all temp data files
    node_ID = [".".join(f.split(".")[:-1]) for f in os.listdir(control_node_id_dir) if f.endswith(".node")]    # get node ID

    try:
        file = open('%s/%s.csv' % (temp_data_dir, node_ID[0]),'w')        # save data in file
        file.write("i:%s,y:%s,u:1" % (node_ID[0], str(setpoint)))
        file.close()
    except:
        pass


# display "min" or "max" on screen
def setpoint_display():
    global displayed_s
    global setpoint

    displayed_s = str(setpoint) + degree + "F"  # add degree symbol

    if setpoint <= 60:
        displayed_s = "MIN"
        setpoint = 60

    elif setpoint >= 90:
        displayed_s = "MAX"
        setpoint = 90
    # elif s < 0 or s > 6:
    #     displayed_s = "NAN"

# initialize global variables
temp = 0.0
displayed_s = str(setpoint)        # initial set point displayed on screen

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
setpoint_display()
draw.rectangle((0,0,width,height), outline=0, fill=0)   # clear image with black box
font = ImageFont.truetype('OpenSans-Bold.ttf', 17)       # font size is 19
draw.text((x, top),"Set Temp: " + displayed_s, font=font, fill=255)
font = ImageFont.truetype('OpenSans-Regular.ttf', 12)       # font size is 18
draw.text((x, top+20),"Room Temp: " + str(temp) + degree + "F",font=font, fill=255)
disp.image(image)   # Display image.
disp.display()
time.sleep(0.2)

old_time = time.time()  # get time before starting while loop
temp = readTemp()
setSetpoint()
saveSetpoint()

# loop forever
while True:
    # keep track of time
    current_time = time.time()
    if current_time - old_time >= 30:        # if 30 seconds have passed, update temperature on screen
        old_time = time.time()
        temp = readTemp()
        setpoint = readSetpoint()
        saveSetpoint()
        setpoint_display()
        draw.rectangle((0,0,width,height), outline=0, fill=0)   # Draw a black filled box to clear the image.
        font = ImageFont.truetype('OpenSans-Bold.ttf', 17)       # font size is 19
        draw.text((x, top),"Set Temp: " + displayed_s, font=font, fill=255)
        font = ImageFont.truetype('OpenSans-Regular.ttf', 12)
        draw.text((x, top+20),"Room Temp: " + str(temp) + degree + "F",font=font, fill=255)
        disp.image(image)   # Display image.
        disp.display()
        time.sleep(0.2)
    else:
        pass

     # check if button 1 was pressed
    if GPIO.input(button1) == 0 and GPIO.input(button2) != 0:
        setpoint -= 1
        setpoint_display()
        saveSetpoint()
        setSetpoint()
        draw.rectangle((0,0,width,height), outline=0, fill=0)   # Draw a black filled box to clear the image.
        font = ImageFont.truetype('OpenSans-Bold.ttf', 17)       # font size is 19
        draw.text((x, top),"Set Temp: " + displayed_s, font=font, fill=255)
        font = ImageFont.truetype('OpenSans-Regular.ttf', 12)
        draw.text((x, top+20),"Room Temp: " + str(temp) + degree + "F",font=font, fill=255)
        disp.image(image)   # Display image.
        disp.display()
        time.sleep(0.1)

    # check if button 2 was pressed
    if GPIO.input(button2) == 0 and GPIO.input(button1) != 0:
        setpoint += 1
        setpoint_display()
        saveSetpoint()
        setSetpoint()
        draw.rectangle((0,0,width,height), outline=0, fill=0)   # Draw a black filled box to clear the image.
        font = ImageFont.truetype('OpenSans-Bold.ttf', 17)       # font size is 19
        draw.text((x, top),"Set Temp: " + displayed_s, font=font, fill=255)
        font = ImageFont.truetype('OpenSans-Regular.ttf', 12)
        draw.text((x, top+20),"Room Temp: " + str(temp) + degree + "F",font=font, fill=255)
        disp.image(image)   # Display image.
        disp.display()
        time.sleep(0.1)

    # if both buttons are pressed, do nothing
    if GPIO.input(button1) == 0 and GPIO.input(button2) == 0:
        start_time = time.time()
        while GPIO.input(button1) == 0 and GPIO.input(button2) == 0:
            elapsed_time = time.time() - start_time
            if elapsed_time >= 3:

                # debug stuff
                IP = subprocess.check_output("hostname -I", shell=True).decode("utf-8")
                cmd = "df -h | awk '$NF==\"/\"{printf \"Disk: %d/%d GB  %s\", $3,$2,$5}'"
                Disk = subprocess.check_output(cmd, shell=True).decode("utf-8")
                script = get_running_scripts()
                dt = datetime.now().strftime('%Y/%m/%d %H:%M:%S')

                draw.rectangle((0,0,width,height), outline=0, fill=0)   # Draw a black filled box to clear the image.
                font = ImageFont.load_default()
                draw.text((x, top+0),"IP: " + IP, font=font, fill=255)
                draw.text((x, top+8), Disk, font=font, fill=255)
                draw.text((x, top+16), "PY: " + script, font=font, fill=255)
                draw.text((x, top+25), dt, font=font, fill=255)

                disp.image(image)   # Display image.
                disp.display()
                time.sleep(5)
                break
            elif elapsed_time >= 10:
                break
            else:
                time.sleep(0.005)
            

    # sleep the code a bit so CPU doesn't choke to death with 100% usage
    time.sleep(0.005)
