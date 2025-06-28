import os
import time
import board
import busio
import gpiozero
import math

from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

import subprocess

class Screen:
    oled_reset_pin = gpiozero.OutputDevice(4, active_high=False)  # GPIO 4 for reset, active low

    WIDTH = 128
    HEIGHT = 64
    BORDER = 1
    CENTRE = (WIDTH // 2, HEIGHT // 2)
    
    i2c = board.I2C()

    def __init__(self, addr: int = 0x3C, refresh_rate: int = 60):

        self.LOOPTIME = 1.0 / refresh_rate

        self.oled_reset_pin.on()
        time.sleep(0.1)  # Delay for a brief moment
        self.oled_reset_pin.off()  # Toggle reset pin low
        time.sleep(0.1)  # Wait for reset
        self.oled_reset_pin.on()  # Turn reset pin back high
    
        self.oled = adafruit_ssd1306.SSD1306_I2C(self.WIDTH, self.HEIGHT, self.i2c, addr=addr)
    
        self.oled.fill(0)
        self.oled.show()
    
        self.image = Image.new("1", (self.oled.width, self.oled.height))
    
        self.canvas = ImageDraw.Draw(self.image)
    
        self.canvas.rectangle((0, 0, self.oled.width, self.oled.height), outline=255, fill=255)
    
        self.font = ImageFont.truetype(os.path.join(os.path.dirname(__file__), 'PixelOperator.ttf'), 16)
    
    def drawCircle(self, centre: tuple[int, int], radius: int, width: int = 0):
        bbox = (int(centre[0] - radius), int(centre[1] - radius), int(centre[0] + radius), int(centre[1] + radius))
        fill = 1 if width == 0 else 0
        self.canvas.ellipse(bbox, fill=fill, outline=int(not fill), width=width)
    
    def start(self):
        
        a = 0
        while True:
            self.canvas.rectangle((self.BORDER, self.BORDER,
                                self.oled.width - self.BORDER * 2, self.oled.height - self.BORDER * 2),
                                outline=0, fill=0)
            
            self.drawCircle(self.CENTRE, 5, 0)
            
            a += 0.15
            x = self.CENTRE[0] + 15 * math.cos(a)
            y = self.CENTRE[1] + 15 * math.sin(a)
            self.drawCircle((x, y), 3, 1)
            
            self.oled.image(self.image)
            self.oled.show()
    
            time.sleep(self.LOOPTIME)
    
if __name__ == "__main__":
    screen = Screen(refresh_rate = 60)
    screen.start()
