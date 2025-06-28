import os
import time
import board
import busio
import gpiozero
import math

from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306

import subprocess

PI_OVER_4 = 0.7853981634
SQRT_2 = 1.414

class Screen:
    oled_reset_pin = gpiozero.OutputDevice(4, active_high=False)  # GPIO 4 for reset, active low

    WIDTH = 128
    HEIGHT = 64
    BORDER = 0
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
        
        self.ballAngle = 0
        self.ballDistance = 15
        self.orientation = 0
        self.position = [0, 0]
        
        self.ticks = 0
    
    def drawCircle(self, centre: tuple[int, int], radius: int, width: int = 0):
        
        bbox = (int(centre[0] - radius), int(centre[1] - radius), int(centre[0] + radius), int(centre[1] + radius))
        fill = 1 if width == 0 else 0
        self.canvas.ellipse(bbox, fill=fill, outline=int(not fill), width=width)

    def drawFOV(self, centre: tuple[int, int], radius: int, direction: int, angle: int, width: int = 0):
        
        bbox = (int(centre[0] - radius), int(centre[1] - radius), int(centre[0] + radius), int(centre[1] + radius))
        fill = 1 if width == 0 else 0
        self.canvas.pieslice(bbox, direction - angle // 2, direction + angle // 2, fill=fill, outline=int(not fill), width=width)

    def drawCross(self, centre: tuple[int, int], radius: int):
        cx = int(centre[0])
        cy = int(centre[1])
        radius = int(radius * SQRT_2)
        self.canvas.line([(-radius + cx, -radius + cy), (radius + cx,  radius + cy)], fill=1, width=1)
        self.canvas.line([(-radius + cx,  radius + cy), (radius + cx, -radius + cy)], fill=1, width=1)

    def drawVector(self, centre: tuple[int, int], magnitude: int, direction: int):
        rd = math.radians(direction)
        x = centre[0] + magnitude * math.cos(rd)
        y = centre[1] + magnitude * math.sin(rd)
        dest = (int(x), int(y))
        self.canvas.line([(int(centre[0]), int(centre[1])), dest], fill=1, width=1)
        r = 5
        da = 3 * PI_OVER_4
        self.canvas.line([dest, (int(x + r * math.cos(rd + da)), int(y + r * math.sin(rd + da)))], fill=1, width=1)
        self.canvas.line([dest, (int(x + r * math.cos(rd - da)), int(y + r * math.sin(rd - da)))], fill=1, width=1)
        

    def clear(self):
        self.canvas.rectangle((self.BORDER, self.BORDER,
                            self.oled.width - self.BORDER - 1, self.oled.height - self.BORDER - 1),
                            outline=0, fill=0)
              
    def update(self):        
        self.oled.image(self.image)
        self.oled.show()

        time.sleep(self.LOOPTIME)
        self.ticks += 1
    
    def eventUpdate(self):
    
        if self.BORDER >= 0:
            self.clear()
        
        self.drawFOV(self.CENTRE, radius=28, direction=self.ballAngle, angle=80, width=1)
        self.drawCircle(self.CENTRE, 5, 0)
        
        ra = math.radians(self.ballAngle)
        x = self.CENTRE[0] + self.ballDistance * math.cos(ra)
        y = self.CENTRE[1] + self.ballDistance * math.sin(ra)
        self.drawCircle((x, y), radius=3, width=1)
        self.update()
    
    def start(self, updateFunction=None):
        
        while True:
            if updateFunction is not None:
                updateFunction()
                continue
            self.eventUpdate()
            
if __name__ == "__main__":
    screen = Screen(refresh_rate = 60)
    screen.start()
