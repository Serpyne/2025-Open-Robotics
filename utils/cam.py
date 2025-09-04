
import sys
import cv2
import numpy as np
import imutils
from math import *
from threading import Thread
import os
sys.path.append(os.path.dirname(__file__))
from classes import Vector
from time import perf_counter as pc

from picamera2 import Picamera2
ON_PI = True
print(ON_PI)

# size = [200, 150]
size = [640, 480]
RESIZE_WIDTH = size[0]
DISPLAY = True

class Circle:
    def __init__(self, center, radius, colour):
        self.center = center
        self.radius = radius
        self.colour = colour
class Rect:
    def __init__(self, x, y, w, h, colour):
        self.x, self.y = x, y
        self.w, self.h = w, h
        self.colour = colour
class Sector:
    def __init__(self, center, radius, start_angle, end_angle, colour):
        self.center = center
        self.radius = radius
        self.start_angle = start_angle
        self.end_angle = end_angle
        self.colour = colour

def lerp(a, b, step=0.1):
    return a + (b - a) * step

class Camera:
    def __init__(self):
        if ON_PI:
            self.stream = Picamera2(0)
            raw_config = self.stream.sensor_modes[0]
            #raw_config["fps"] = 60
            print(raw_config)
            config = self.stream.create_video_configuration(
                main={"format": "XRGB8888", "size": size},
                raw=raw_config,
                buffer_count=6,
                controls={"FrameRate": raw_config["fps"]},
            )
            self.stream.configure(config)
            self.stream.controls.ExposureTime = 8410
            self.stream.controls.Saturation = 3
        else:
            self.stream = VideoStream()

        self._frame = None
        self.frame = None

        self.pos = None
        self.radius = None
        self.yellow_goal_mask = None
        self.blue_goal_mask = None

        self.yellow_center = None
        self.blue_center = None
        self.yellow_angle = None
        self.blue_angle = None
        
        self.distance = None
        self.angle = None
        # Lerp stuff
        self.targetAngle = None
        self.targetDistance = None

        self.true_distance_map = {
            "a": -0.5382952459001382,
            "k": 94.8194330930013
        }

        self.center = [320, 240]
        
        self.body_masks = [
            #Circle((318, 250), 123, (0, 255, 0)),
            Sector((318, 250), 123, -(180-40), 180-40, (0, 255, 0)),
            Rect(300, 355, 40, 32, (0, 255, 0)),
            Rect(318-85, 250-70
            , 85, 140, (0, 255, 0))
            #Rect(435, 210, 24, 90, (0, 255, 0))
        ]

        self.running = False

    def read(self) -> cv2.typing.MatLike:
        if ON_PI:
            return self.stream.capture_array()
        return self.stream.read()

    def draw_body_masks(self, frame, filled=True):
        _fill = 1
        if filled: _fill = -1
        
        for bmask in self.body_masks:
            if type(bmask) == Circle:
                cv2.circle(frame, bmask.center, bmask.radius, bmask.colour, _fill)
            elif type(bmask) == Rect:
                cv2.rectangle(frame, (bmask.x, bmask.y), (bmask.x + bmask.w, bmask.y + bmask.h), bmask.colour, _fill)
            elif type(bmask) == Sector:
                cv2.ellipse(frame, bmask.center, (bmask.radius, bmask.radius),
                0, bmask.start_angle, bmask.end_angle, bmask.colour, _fill)

    def get_mask(self, frame) -> cv2.typing.MatLike:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        self.draw_body_masks(rgb)

        ball_lower = (175, 0, 0)
        ball_upper = (255, 90, 35)
        mask = cv2.inRange(rgb, ball_lower, ball_upper)

        return mask
    
    def calculate_true_distance(self, radius):
        return self.true_distance_map["k"] * pow(radius, self.true_distance_map["a"])
        
    def process_frame(self, frame) -> cv2.typing.MatLike:
        mask = self.get_mask(frame)
        contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)
        
        if DISPLAY:
            self.draw_body_masks(frame, 0)
            cv2.drawMarker(frame, self.center, (255, 0, 255))
        
        if len(contours) == 0:
            self.angle = self.distance = None
            return frame
            
        points = []
        contours = sorted(contours, key=lambda x: x.size, reverse=True)
        
        prev = None
        for i in range(len(contours)):
            cnt = contours[i]
            if cnt.size < 30: continue
                
            M = cv2.moments(cnt)
            if M["m00"] == 0: continue
            center = Vector(M["m10"] / M["m00"], M["m01"] / M["m00"])
            if prev is None: dist_to_last_contour = 0
            else:            dist_to_last_contour = (center - prev).magnitude
                
            if dist_to_last_contour > 120: continue

            prev = center.copy()
            if DISPLAY: cv2.drawMarker(frame, center.int(), (255, 0, 255))
            points += [x for x in cnt]
                
        if len(points) <= 4:
            self.angle = self.distance = None
            return frame
            
        c = cv2.convexHull(np.array(points, dtype=np.int32))
        
        if c.size <= 4 * 2: 
            self.angle = self.distance = None
            return frame

        ellipse = cv2.fitEllipse(c)
        center, size, angle = ellipse
        
        self.pos = Vector(center)
        delta_pos = self.pos.x - self.center[0], self.pos.y - self.center[1]
        self.targetAngle = -atan2(delta_pos[1], delta_pos[0])
        radial_distance = sqrt(delta_pos[0]**2 + delta_pos[1]**2)
        self.radius = size[0] * size[1]
        
        self.targetDistance = self.calculate_true_distance(self.radius / radial_distance)
        
        if self.angle is None: self.angle = 0
        if self.distance is None: self.distance = 0
        #self.angle = lerp(self.angle, self.targetAngle, step=0.05)
        self.angle = self.targetAngle
        self.distance = lerp(self.distance, self.targetDistance, step=0.05)
        
        if DISPLAY:
            for i in range(len(contours)):
                cv2.drawContours(frame, contours, i, (0, 255, 0))

            pos = [int(center[0]), int(center[1])]

            cv2.ellipse(frame, ellipse, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.drawMarker(frame, pos, (0, 0, 255))
            cv2.line(frame, self.center, pos, (255,0,0), 5)
            
        return frame
    
    def start_event_loop(self):
        if ON_PI: self.stream.start()
        else: self.stream = self.stream.start()
        
        self.running = True
        def _event_loop():
            while self.running:
                self._frame = self.read()
                if self._frame is None: continue
                if self._frame.size == 0: self._frame = None; continue
                self._frame = imutils.resize(self._frame, width=640)

                self.frame = self.process_frame(self._frame)

        Thread(target=_event_loop, daemon=True).start()

    def show_debug_screen(self):
        def main():
            while True:
                if self.frame is None: continue
                if DISPLAY:
                    cv2.imshow("test", self.frame)
                    cv2.waitKey(1)
                    
                    # if None in [self.angle, self.distance]:
                        # print("Ball covered")
                    # else:
                        # print(f"Angle: {int(degrees(camera.angle))} | Distance: {int(camera.distance)}")
        try:
            Thread(target=main).start()
        
        except KeyboardInterrupt:
            self.stop()
            cv2.destroyAllWindows()
            sys.exit()

    def stop(self):
        self.running = False
        if ON_PI:
            self.stream.close()
        else:
            self.stream.stop()

if __name__ == "__main__":
    camera = Camera()
    camera.start_event_loop()
    camera.show_debug_screen()
