import sys
import os
import asyncio
import math

from flask import Flask, Response

parent_dir = "\\".join(os.path.dirname(__file__).split("\\")[:-1])
sys.path.append(parent_dir)
from main import mainloop

import cv2

async def main(camera):
    # Begins camera stream and starts camera image processing
    camera.start_event_loop()
        
    app = Flask(__name__)
    
    def generate_frames():
        while True:
            _, buffer = cv2.imencode('.jpg', camera.frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    
    @app.route('/')
    def index():
        return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    mainloop(main, motors=False, camera=True)

