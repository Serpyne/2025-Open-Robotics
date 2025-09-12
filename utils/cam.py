
import sys
import cv2
import numpy as np
import imutils
from math import *
from threading import Thread
import readline
import os
sys.path.append(os.path.dirname(__file__))
from classes import Vector
from time import perf_counter as pc

from picamera2 import Picamera2

size = [640, 480]
RESIZE_WIDTH = size[0]
DISPLAY = False

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
        self.stream = Picamera2(0)
        
        print("All formats: ");[print(x, "\n") for x in self.stream.sensor_modes]
        
        raw_config = self.stream.sensor_modes[0]
        raw_config["fps"] = 120.05
        raw_config["size"] = tuple(size)
        # ~ raw_config["crop_limits"] = (696, 528, 2664, 1980)
        
        print(f"\nCurrent format: \n{raw_config}\n")
        
        config = self.stream.create_video_configuration(
            main={"format": "XRGB8888", "size": size},
            raw=raw_config,
            buffer_count=6,
            controls={"FrameRate": raw_config["fps"]},
            #queue=True
        )
        self.stream.configure(config)
        self.stream.controls.ExposureTime = 60000#8410
        self.stream.controls.Saturation = 3

        self._frame = None
        self.frame = None

        self.pos = None
        self.radius = None
        
        self.ball_lower = (200, 0, 0)
        self.ball_upper = (255, 90, 35)
        self.yellow_lower = (47, 55, 0)
        self.yellow_upper = (76, 100, 25)
        self.blue_lower = (0, 20, 80)
        self.blue_upper = (10, 60, 160)
        
        self.yellow_goal_mask = None
        self.blue_goal_mask = None
        self.yellow_center = None
        self.blue_center = None
        self.yellow_angle = None
        self.blue_angle = None
        
        self.true_yellow_distance = None
        self.yellow_distance = None
        self.true_blue_distance = None
        self.blue_distance = None
        
        self.distance = None
        self.angle = None
        # Lerp stuff
        self.targetAngle = None
        self.targetDistance = None

        self.true_distance_map = {
            "a": -0.5382952459001382,
            "k": 94.8194330930013
        }

        self.center = [size[0] // 2, size[1] // 2]
        
        self.body_masks: list = [Circle(self.center, 130, (0, 255, 0))]

        self.running = False
        self.dt = 0
        self.prev_time = pc()

    def read(self) -> cv2.typing.MatLike:
        return self.stream.capture_array()

    def set_masks(self, masks: list):
        "{type, args*}"
        self.body_masks.clear()
        for mask in masks:
            if mask["type"] == "circle":
                self.body_masks.append(Circle(mask["center"], mask["radius"], mask["colour"]))
            elif mask["type"] == "rect":
                self.body_masks.append(Rect(mask["x"], mask["y"], mask["w"], mask["h"], mask["colour"]))
            elif mask["type"] == "sector":
                self.body_masks.append(Sector(mask["center"], mask["radius"], mask["startAngle"], mask["endAngle"], mask["colour"]))
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
        
        mask = cv2.inRange(rgb, self.ball_lower, self.ball_upper)
        self.yellow_goal_mask = cv2.inRange(rgb, self.yellow_lower, self.yellow_upper)
        self.blue_goal_mask = cv2.inRange(rgb, self.blue_lower, self.blue_upper)

        return mask
    
    def calculate_true_distance(self, x, a=677.87957, b=325.553):
        return pow(a/(x - b), 2)
        
    def find_biggest_conglomerate_contour(self, mask,
                    max_dist_to_last_contour: float = 120, min_contour_size: int = 30, conglomerate_threshold: int = 8):
        
        contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)
        
        if len(contours) == 0:
            return None
        
        points = []
        contours = sorted(contours, key=lambda x: x.size, reverse=True)
        
        prev = None
        for i in range(len(contours)):
            cnt = contours[i]
            if cnt.size < min_contour_size: continue
                
            M = cv2.moments(cnt)
            if M["m00"] == 0: continue
            center = Vector(M["m10"] / M["m00"], M["m01"] / M["m00"])
            if prev is None: dist_to_last_contour = 0
            else:            dist_to_last_contour = (center - prev).magnitude
                
            if dist_to_last_contour > max_dist_to_last_contour: continue

            prev = center.copy()
            points += [x for x in cnt]
                
        if len(points) <= 4:
            return None
            
        conglomerate = cv2.convexHull(np.array(points, dtype=np.int32))
        if conglomerate.size <= conglomerate_threshold:
            return None    
        
        return conglomerate, contours
    
    def _process_ball(self, frame):
        mask = self.get_mask(frame)
        c_pair = self.find_biggest_conglomerate_contour(mask)
        
        self.draw_body_masks(frame, 0)
        cv2.drawMarker(frame, self.center, (255, 0, 255))
                
        if c_pair is None:
            self.angle = self.distance = None
            return
            
        conglomerate, contours = c_pair
        
        ellipse = cv2.fitEllipse(conglomerate)
        center, size, angle = ellipse
        
        # BALL LOCATION UPDATING
        
        self.pos = Vector(center)
        delta_pos = self.pos.x - self.center[0], self.pos.y - self.center[1]
        self.targetAngle = degrees(-atan2(delta_pos[1], delta_pos[0]))
        radial_distance = sqrt(delta_pos[0]**2 + delta_pos[1]**2)
        self.radius = size[0] * size[1]
        
        self.targetDistance = self.calculate_true_distance(radial_distance)
        
        if self.angle is None: self.angle = self.targetAngle
        self.angle = self.angle + ((self.targetAngle - self.angle + 180) % 360 - 180) * .5
        if self.distance is None: self.distance = self.targetDistance
        self.distance = lerp(self.distance, self.targetDistance, step=0.041)
        
        if not DISPLAY: return
        
        for i in range(len(contours)):
            cv2.drawContours(frame, contours, i, (0, 255, 0))

        pos = [int(center[0]), int(center[1])]

        cv2.ellipse(frame, ellipse, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.drawMarker(frame, pos, (0, 0, 255))
        cv2.line(frame, self.center, pos, tuple(self.ball_upper[::-1]), 5)
        
    def _process_goals(self, frame, max_dist_to_last_contour = 200, min_contour_size = 120):
        c_pair = self.find_biggest_conglomerate_contour(self.yellow_goal_mask,
                            max_dist_to_last_contour=max_dist_to_last_contour, min_contour_size=min_contour_size)
        
        if c_pair is None:
            self.yellow_angle = None
            self.yellow_center = None
            self.yellow_distance = None
        else:
            conglomerate, contours = c_pair
            
            M = cv2.moments(conglomerate)
            if M["m00"] == 0:
                self.yellow_angle = None
                self.yellow_center = None
                self.yellow_distance = None
            else:
                self.yellow_center = [int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])]
            
                delta_pos = self.yellow_center[0] - self.center[0], self.yellow_center[1] - self.center[1]
                self.yellow_angle = degrees(-atan2(delta_pos[1], delta_pos[0]))
                
                pixel_dist = abs(cv2.pointPolygonTest(conglomerate, self.center, True))
                
                self.true_yellow_distance = self.calculate_true_distance(pixel_dist)
                if self.yellow_distance is None: self.yellow_distance = self.true_yellow_distance
                else: self.yellow_distance = lerp(self.yellow_distance, self.true_yellow_distance, 0.1)
                
                if DISPLAY:
                    for i in range(len(contours)):
                        cv2.drawContours(frame, contours, i, (0, 255, 0))
                    cv2.drawContours(frame, [conglomerate], 0, (255, 255, 255))

                    cv2.drawMarker(frame, self.yellow_center, (0, 0, 255))
                    cv2.line(frame, self.center, self.yellow_center, tuple(self.yellow_upper[::-1]), 5)
                
        c_pair = self.find_biggest_conglomerate_contour(self.blue_goal_mask,
                            max_dist_to_last_contour=max_dist_to_last_contour,min_contour_size=min_contour_size)
        
        if c_pair is None:
            self.blue_angle = None
            self.blue_center = None
        else:
            conglomerate, contours = c_pair
            
            M = cv2.moments(conglomerate)
            if M["m00"] == 0:
                self.blue_center = None
            else:
                self.blue_center = [int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"])]
            
                delta_pos = self.blue_center[0] - self.center[0], self.blue_center[1] - self.center[1]
                self.blue_angle = degrees(-atan2(delta_pos[1], delta_pos[0]))
                
                pixel_dist = abs(cv2.pointPolygonTest(conglomerate, self.center, True))
                
                self.true_blue_distance = self.calculate_true_distance(pixel_dist)
                if self.blue_distance is None: self.blue_distance = self.true_blue_distance
                else: self.blue_distance = lerp(self.blue_distance, self.true_blue_distance, 0.1)
                
                if DISPLAY:
                    for i in range(len(contours)):
                        cv2.drawContours(frame, contours, i, (0, 255, 0))
                    cv2.drawContours(frame, [conglomerate], 0, (255, 255, 255))

                    cv2.drawMarker(frame, self.blue_center, (0, 0, 255))
                    cv2.line(frame, self.center, self.blue_center, tuple(self.blue_upper[::-1]), 5)
    def process_frame(self, frame) -> cv2.typing.MatLike:
        frame = cv2.circle(frame, [305, 250], 270, (255, 255, 255), 5)
        self._process_ball(frame)
        self._process_goals(frame)
        return frame
    
    def start_event_loop(self):
        self.stream.start()
        
        self.running = True
        def _event_loop():
            while self.running:
                curr = pc()
                self.dt = curr - self.prev_time
                self.prev_time = curr
                
                self._frame = self.read()
                if self._frame is None: continue
                if self._frame.size == 0: self._frame = None; continue
                
                # ~ if self._frame.shape[1] != RESIZE_WIDTH:
                    # ~ self._frame = imutils.resize(self._frame, width=RESIZE_WIDTH)

                self.frame = self.process_frame(self._frame)

        Thread(target=_event_loop, daemon=True).start()

    def show_debug_screen(self):
        global DISPLAY
        DISPLAY = True
        
        def main():
            while True:
                if self.frame is None: continue
                if DISPLAY:
                    cv2.imshow("Camera", self.frame)
                    if self.dt > 0.0001:
                        cv2.setWindowTitle("Camera", f"{int(1//self.dt)}")
                    cv2.waitKey(1)
        try:
            Thread(target=main).start()
            
            if 0:
                while True:
                    s = input("> ")
                    if len(s) <= 2:
                        print(f"self.ball_lower = {self.ball_lower}")
                        print(f"self.ball_upper = {self.ball_upper}")
                        print(f"self.blue_lower = {self.blue_lower}")
                        print(f"self.blue_upper = {self.blue_upper}")
                        print(f"self.yellow_lower = {self.yellow_lower}")
                        print(f"self.yellow_upper = {self.yellow_upper}")
                        continue
                    s = s.lower()
                    if s[0] not in "byul":
                        print("invalid")
                        continue
                    try:
                        if s[0] in "by":
                            t = tuple([int(x) for x in s[2:].split(',')])[:3]
                        else:
                            t = tuple([int(x) for x in s[1:].split(',')])[:3]
                    except:
                        continue
                    if s[0] == "b":
                        if s[1] == "l":
                            self.blue_lower = t
                        elif s[1] == "u":
                            self.blue_upper = t
                    elif s[0] == "y":
                        if s[1] == "l":
                            self.yellow_lower = t
                        elif s[1] == "u":
                            self.yellow_upper = t
                            
                    elif s[0] == "l":
                        self.ball_lower = t
                    elif s[0] == "u":
                        self.ball_upper = t
        
        except KeyboardInterrupt:
            self.stop()
            cv2.destroyAllWindows()
            sys.exit()

    def stop(self):
        self.running = False
        self.stream.close()

if __name__ == "__main__":
    DISPLAY = True
    camera = Camera()
    camera.start_event_loop()
    camera.show_debug_screen()
