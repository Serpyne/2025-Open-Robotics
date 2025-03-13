"""
Module to turn the fan on the Raspberry Pi 5 on or off.

pinctrl: https://github.com/raspberrypi/utils/tree/master/pinctrl

Setting GPIO pin output:
$ pinctrl [-p] [-v] [-e]
- p: GPIO pin
- op: output
- dh: drive high (1)
- dl: drive low(0)

`dl` will turn the fan on, while `dh` will turn the fan off.
"""


from os import system

ON_COMMAND = "pinctrl FAN_PWM op dl"
OFF_COMMAND = "pinctrl FAN_PWM op dh"
GET_COMMAND = "pinctrl get FAN_PWM"

class Fan:
    def on(self):
        system(ON_COMMAND)
    def off(self):
        system(OFF_COMMAND)
    def get(self) -> int:
        return system(GET_COMMAND)