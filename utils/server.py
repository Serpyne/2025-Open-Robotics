"""
Flask server to handle the calibration control panel.
"""

from flask import Flask, render_template, jsonify, request, Response
import logging
from aiortc import RTCPeerConnection, RTCSessionDescription
import uuid
import asyncio
import logging
import time

from scipy.optimize import curve_fit
import numpy as np
from matplotlib import use as mpluse
import matplotlib.pyplot as plt
from io import BytesIO

from os.path import join, dirname
import base64
import cv2
import json
import colorsys
from time import perf_counter

DEBUG = False

PNG_START = "data:image/png;base64,"
save_path = join(dirname(__file__), "save.json")

def rgb_to_hsv(rgb) -> tuple:
    normal_rgb = [i / 255 for i in rgb]
    normal_hsv = colorsys.rgb_to_hsv(*normal_rgb)
    return (round(360 * normal_hsv[0]), round(255 * normal_hsv[1]), round(255 * normal_hsv[2]))
    
class Server(Flask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._define_routes()

        self.preview = None
        self.show_preview = False
        
        self.radius = None
        self.radial_distance = None
        self.distance = None
        self.angle = None
        self.x_offset = None
        self.fps = None
        
        # Calibration parameters
        self.a = self.k = None
        self.m = self.c = None
        with open(join(dirname(__file__), "save.json"), "r") as f:
            data = json.load(f)
            self.lower = data["color"]["lower"]
            self.upper = data["color"]["upper"]
            self.mask_radius = data["maskRadius"]

    def gen_preview(self):
        """
        Video Stream
        """
        old_preview = None
        while self.show_preview:
            if self.preview is not None:
                # if old_preview is not None:
                #     if not np.array_equal(old_preview, self.preview):
                _, img_arr = cv2.imencode(".jpeg", self.preview)
                img_bytes = img_arr.tobytes()
                image = (b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + img_bytes + b'\r\n')
                yield image
                # old_preview = self.preview.copy()

    def _define_routes(self):
        # def offer():
        #     loop = asyncio.new_event_loop()
        #     asyncio.set_event_loop(loop)
            
        #     future = asyncio.run_coroutine_threadsafe(offer_async(), loop)
        #     return future.result()
        
        # async def offer_async():
        #     params = await request.json
        #     offer = RTCSessionDescription(sdp=params["sdp"], type=params["type"])

        #     # Create an RTCPeerConnection instance
        #     pc = RTCPeerConnection()

        #     # Generate a unique ID for the RTCPeerConnection
        #     pc_id = "PeerConnection(%s)" % uuid.uuid4()
        #     pc_id = pc_id[:8]

        #     # Create and set the local description
        #     await pc.createOffer(offer)
        #     await pc.setLocalDescription(offer)

        #     # Prepare the response data with local SDP and type
        #     response_data = {"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}

        #     return jsonify(response_data)
        
        # # Route to handle the offer request
        # @self.route('/offer', methods=['POST'])
        # def offer_route():
        #     return offer()
        
        @self.route("/")
        def index():
            with open(save_path, "r") as f:
                data = json.load(f)
                dist = data["dist"]
                angle = data["angle"]
                f.close()
            return render_template("index.html", a=dist["a"], k=dist["k"], m=angle["m"], c=angle["c"])
            
        @self.route("/maskRadius", methods=["POST"])
        def mask_radius():
            with open(join(dirname(__file__), "save.json"), "r") as f:
                data = json.load(f)
            self.mask_radius = data["maskRadius"]
            return jsonify({"radius": self.mask_radius})
        
        @self.route("/setMaskRadius", methods=["POST"])
        def set_mask_radius():
            data = json.loads(request.data)
            radius = data["radius"]

            try:
                radius = int(radius)
                if radius > 0:
                    self.mask_radius = radius
                    with open(join(dirname(__file__), "save.json"), "r") as f:
                        data = json.load(f)
                    data["maskRadius"] = self.mask_radius
                    with open(join(dirname(__file__), "save.json"), "w") as f:
                        json.dump(data, f, sort_keys=True, indent=4)

            except Exception as exc:
                pass

            return jsonify({})

        @self.route("/fps", methods=["POST"])
        def fps():
            return jsonify({"fps": self.fps})
 
        @self.route("/radius", methods=["POST"])
        def radius():
            return jsonify({"radius": self.radius, "radialDistance": self.radial_distance})
 
        @self.route("/distance", methods=["POST"])
        def distance():
            return jsonify({"distance": self.distance})
 
        @self.route("/colors", methods=["POST"])
        def colors():
            return jsonify({"lower": self.lower, "upper": self.upper})
 
        @self.route("/setColors", methods=["POST"])
        def set_colors():
            data = json.loads(request.data)
            try:
                self.lower = tuple([float(c) for c in data["lower"]])
                self.upper = tuple([float(c) for c in data["upper"]])
            except ValueError:
                return jsonify({})
            with open(join(dirname(__file__), "save.json"), "r") as f:
                data = json.load(f)
            data["color"]["lower"] = self.lower
            data["color"]["upper"] = self.upper
            with open(join(dirname(__file__), "save.json"), "w") as f:
                json.dump(data, f, sort_keys=True, indent=4)
            return jsonify({})
 
        @self.route("/angle", methods=["POST"])
        def angle():
            return jsonify({"angle": self.angle})
 
        @self.route("/xOffset", methods=["POST"])
        def x_offset():
            return jsonify({"xOffset": self.x_offset})

        @self.route("/hidePreview", methods=["POST"])
        def hide_preview():
            self.show_preview = False
            return jsonify({})
        
        @self.route("/preview")
        def preview():
            self.show_preview = True
            
            return Response(self.gen_preview(), mimetype='multipart/x-mixed-replace; boundary=frame')
         
        @self.route("/fitAngle", methods=["POST"])
        def fit_angle():
            data = json.loads(request.data)

            def func(x, m, c):
                return m * x + c
        
            self.x_data = data["x"]
            self.y_data = data["trueX"]

            self.initial_guess = [1.0, 0.0]
            params, covariance = curve_fit(func, self.x_data, self.y_data, p0=self.initial_guess)

            self.m, self.c = params
            
            with open(save_path, "r") as f:
                data = json.load(f)
                f.close()
            data["angle"] = {"m": self.m, "c": self.c}
            with open(save_path, "w") as f:
                json.dump(data, f, sort_keys=True, indent=4)
                f.close()

            x_fit = np.linspace(min(self.x_data), max(self.x_data), 137)
            y_fit = func(x_fit, self.m, self.c)

            plt.figure(figsize=(16, 12)) 
            plt.scatter(self.x_data, self.y_data, label="Data")
            plt.plot(x_fit, y_fit, label="Linear Fit", color= "red")
            plt.xticks(fontsize=15) 
            plt.yticks(fontsize=15)
            plt.xlabel("Camera X",fontsize=17)
            plt.ylabel("True X",fontsize=17)
            plt.title("Camera X vs True X",fontsize=22)

            equation = f"y = {self.m:.2f}x + {self.c:.2f}"
            
            plt.text(50, 16, equation, fontsize=19, color='red',
                bbox={'facecolor': 'white', 'alpha': 0.7, 'edgecolor': 'gray'})
            img = BytesIO()
            plt.savefig(img, format="png")
            plt.savefig(join(dirname(__file__), "static/angle.png"), format="png")
            img.seek(0)
            img_base64 = PNG_START + base64.b64encode(img.read()).decode("utf-8")

            return jsonify({"m": self.m, "c": self.c, "graph": img_base64})

        @self.route("/fitDist", methods=["POST"])
        def fit_dist():
            data = json.loads(request.data)

            self.x_data = data["radii"]
            self.y_data = data["distance"]

            def func(x, k, a):
                return k * pow(x, a)
        
            self.initial_guess = [2000.0, -1.0]
            params, covariance = curve_fit(func, self.x_data, self.y_data, p0=self.initial_guess)

            self.k, self.a = params
            
            with open(save_path, "r") as f:
                data = json.load(f)
                f.close()
            data["dist"] = {"k": self.k, "a": self.a}
            with open(save_path, "w") as f:
                json.dump(data, f, sort_keys=True, indent=4)
                f.close()

            x_fit = np.linspace(min(self.x_data), max(self.x_data), 137)
            y_fit = func(x_fit, self.k, self.a)

            plt.figure(figsize=(16, 12)) 
            plt.scatter(self.x_data, self.y_data, label="Data")
            plt.plot(x_fit, y_fit, label="Power Series Fit", color= "red")
            plt.xticks(fontsize=15) 
            plt.yticks(fontsize=15)
            plt.xlabel("Radius",fontsize=17)
            plt.ylabel("Distance",fontsize=17)
            plt.title("Radius vs Distance",fontsize=22)

            equation = f"y = {self.k:.2f}x^{self.a:.2f}"
            
            plt.text(50, 16, equation, fontsize=19, color='red',
                bbox={'facecolor': 'white', 'alpha': 0.7, 'edgecolor': 'gray'})
            img = BytesIO()
            plt.savefig(img, format="png")
            plt.savefig(join(dirname(__file__), "static/dist.png"), format="png")
            img.seek(0)
            img_base64 = PNG_START + base64.b64encode(img.read()).decode("utf-8")

            return jsonify({"k": self.k, "a": self.a, "graph": img_base64})

        @self.route("/calibrateColors", methods=["POST"])
        def calibrate_colors():
            colors = json.loads(request.data)
            
            lower = [255, 255, 255]
            upper = [0, 0, 0]
            for color in colors:
                # Convert from RGB to HSV
                color = rgb_to_hsv([int(x) for x in color[1:-1].split(", ")])
                for i in range(3):
                    if color[i] < lower[i]:
                        lower[i] = color[i]
                    if color[i] > upper[i]:
                        upper[i] = color[i]
                    
            # Save to save.json
            with open(save_path, "r") as f:
                data = json.load(f)
                f.close()
            data["color"] = {"lower": lower, "upper": upper}
            with open(save_path, "w") as f:
                json.dump(data, f, sort_keys=True, indent=4)
                f.close()
                
            self.lower = lower
            self.upper = upper
            
            return jsonify({})

    def start(self):
        # Agg is a non-interactive backend.
        # Prevents the error when initialising a MPL figure.
        try:
            mpluse("agg")
            
            # Disable console messages
            if DEBUG == False:
                log = logging.getLogger('werkzeug')
                log.setLevel(logging.ERROR)
                
            self.run(port=8080, host="0.0.0.0")
            
        except Exception as exc:
            print(exc)
