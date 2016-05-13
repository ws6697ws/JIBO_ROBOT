#!/usr/bin/env python


import time
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(26, GPIO.OUT)

p = GPIO.PWM(26, 50)
p.start(0)
try:
    while 1:
        for dc in range(0, 181, 10):
            p.ChangeDutyCycle(2.5 + 10 * dc / 180)
            time.sleep(0.02)
            p.ChangeDutyCycle(0)
            time.sleep(0.2)
        for dc in range(180, -1, -10):
            p.ChangeDutyCycle(2.5 + 10 * dc / 180)
            time.sleep(0.02)
            p.ChangeDutyCycle(0)
            time.sleep(0.2)
except KeyboardInterrupt:
    pass
p.stop()
GPIO.cleanup()
