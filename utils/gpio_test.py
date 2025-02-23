import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)

class position:
    SWITCH_UP = 0x00
    SWITCH_MIDDLE = 0x01
    SWITCH_DOWN = 0x02
    
switch_middle = 11
switch_up = 13
GPIO.setup(switch_middle, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(switch_up, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
while True:
    switch_position = GPIO.input(switch_up) + GPIO.input(switch_middle)
    match switch_position:
        case position.SWITCH_UP: print("e")
        case position.SWITCH_MIDDLE: print("f")
        case position.SWITCH_DOWN: print("g")
    time.sleep(0.1)
