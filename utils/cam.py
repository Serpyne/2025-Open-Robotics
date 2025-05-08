
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

try:
    from picamera2 import Picamera2
    ON_PI = True
except:
    from imutils.video import VideoStream
    ON_PI = False

size = [200, 150]#[640, 480]
RESIZE_WIDTH = size[0]
DISPLAY = True

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
            self.stream.controls.ExposureTime = 9000
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

        self.center = [320, 480-20]
        
        self.running = False

    def read(self) -> cv2.typing.MatLike:
        if ON_PI:
            return self.stream.capture_array()
        return self.stream.read()

    def get_mask(self, frame) -> cv2.typing.MatLike:
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        cv2.circle(rgb, (320, 480), 160, (0,255,0), -1)

        ball_lower = (175, 0, 0)
        ball_upper = (255, 90, 35)
        mask = cv2.inRange(rgb, ball_lower, ball_upper)

        return mask
    
    def process_frame(self, frame) -> cv2.typing.MatLike:
        mask = self.get_mask(frame)
        contours = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(contours)
        
        if DISPLAY: cv2.drawMarker(frame, self.center, (0, 0, 255))
        if len(contours) == 0: return frame
            
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
                
        if len(points) <= 4: return frame
        c = cv2.convexHull(np.array(points, dtype=np.int32))
        
        if c.size <= 4 * 2: return frame

        ellipse = cv2.fitEllipse(c)
        center, size, angle = ellipse
        
        self.pos = Vector(center)
        delta_pos = self.pos.x - self.center[0], self.pos.y - self.center[1]
        self.angle = -atan2(delta_pos[1], delta_pos[0])
        self.distance = sqrt(delta_pos[0]**2 + delta_pos[1]**2)
        self.radius = size[0] * size[1]
        
        if DISPLAY:   
            for i in range(len(contours)):
                cv2.drawContours(frame, contours, i, (0, 255, 0))

            cv2.ellipse(frame, ellipse, (255, 255, 255), 1, cv2.LINE_AA)
            cv2.drawMarker(frame, [int(center[0]), int(center[1])], (0, 0, 255))
                     
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

    def stop(self):
        self.running = False
        if ON_PI:
            self.stream.close()
        else:
            self.stream.stop()

def main():
    while True:
        if camera.frame is None: continue
        if DISPLAY:
            cv2.imshow("test", camera.frame)
            cv2.waitKey(1)

if __name__ == "__main__":
    try:
        camera = Camera()
        camera.start_event_loop()
        Thread(target=main).start()
    
    except KeyboardInterrupt:
        camera.stop()
        cv2.destroyAllWindows()
        sys.exit()
