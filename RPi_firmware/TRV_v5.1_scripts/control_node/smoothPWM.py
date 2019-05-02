# -*- coding: utf-8 -*-

# This script sets (via PWM) a 270° servo (LD-27MG/DS3218MG) attached to a
# Honeywell thermostatic radiator valve control unit T100B1035/T104B1038

# Developed by Akram Ali
# Last updated on: 4/25/2018

import RPi.GPIO as GPIO
import time
import Adafruit_GPIO.SPI as SPI
import Adafruit_PCA9685

pwm = Adafruit_PCA9685.PCA9685()        # create Adafruit library object
pwm.set_pwm_freq(60)        # Set frequency to 60hz, good for servos.
sp = 635      # initialize pwm value
n = 0
while True:
    # time.sleep(5)      # sleep 10 secs to let other stuff run in bg
    #
    # if s == '0':
    #     sp = 635
    # elif s == '1':
    #     sp = 561
    # elif s == '2':
    #     sp = 482
    # elif s == '3':
    #     sp = 403
    # elif s == '4':
    #     sp = 323
    # elif s == '5':
    #     sp = 244
    # elif s == '6':
    #     sp = 150
    # else:
    #     sp = 635

    # set servo PWM based on setpoint
    if sp >= 150 and sp <= 635:
        pwm.set_pwm(0, 0, sp)
        sp = sp - n
        n = n + 1
    elif sp < 150:
        sp = 150
    elif sp > 635:
        sp = 635
    time.sleep(0.05)
    print (sp)
