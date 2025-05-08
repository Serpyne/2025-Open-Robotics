import sys
import os
import asyncio
import math

from flask import Flask, Response
from picamera2 import Picamera2

parent_dir = "\\".join(os.path.dirname(__file__).split("\\")[:-1])
sys.path.append(parent_dir)
from main import mainloop

import cv2

app = Flask(__name__)
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (200, 150)}))
picam2.start()

def generate_frames():
    while True:
        frame = picam2.capture_array("main")
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
app.run(host='0.0.0.0', port=5000)

# async def main():
#     # Begins camera stream and starts camera image processing
#     # camera.start_event_loop()
#     ...
    
    
# if __name__ == "__main__":
#     mainloop(main, motors=False, camera=False)

