#
# Worker script runs on start-up
# Runs the separate pipeline to control the main script
# Allows users to upload and run scripts on the robot (without restarting the PI)
#

import http.server
import socketserver
import os
try:
    import cgi
    print("On Raspberry Pi 5")
except:
    print("On Laptop")
import sys
import signal
import subprocess
import random
import asyncio
import websockets
import time
import json
from threading import Thread
from string import ascii_letters
import shutil

PORT = 8000

def random_string(count):
    return "".join([random.choice(ascii_letters) for i in range(count)])

class CustomServer(socketserver.TCPServer):
    allow_reuse_address = True
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.proc = None

class CustomHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        if self.path == '/upload':
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={'REQUEST_METHOD': 'POST'}
            )

            if not form['file'].filename:
                self.send_response(303)
                self.send_header('Location', '/')
                self.end_headers()
                return
            
            filename = form['file'].filename
            data = form['file'].file.read()
            
            with open(os.path.join('uploads', filename), 'wb') as f:
                f.write(data)
            
            self.send_response(303)
            self.send_header('Location', '/')
            self.end_headers()
        elif self.path == '/save':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            filename, content = post_data.split(':', 1)
            
            with open(os.path.join('uploads', filename), 'w') as f:
                f.write(content)
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"File saved successfully")
        elif self.path == '/rename':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('-utf-8')
            filename, new_name = post_data.split(":")
            self.send_response(200)
            self.end_headers()
            if not new_name: return
            
            if len(new_name) < 3:
                new_name += ".py"
            else:
                if new_name[-3:] != ".py":
                    new_name += ".py"
                    
            os.rename(os.path.join('uploads', filename), os.path.join('uploads', new_name))
            self.wfile.write(new_name.encode())

        elif self.path == '/execute':
            content_length = int(self.headers['Content-Length'])
            filename = self.rfile.read(content_length).decode('-utf-8')
            self.send_response(200)
            self.end_headers()
            res = toggle_process(filename)
            if res: self.wfile.write(res.encode())

        elif self.path == '/bt':
            content_length = int(self.headers['Content-Length'])
            print(f"Content Length: {content_length}")
            if content_length == 0:
                # Get BT
                self.send_response(200)
                self.end_headers()
                with open(os.path.join(os.path.dirname(__file__), "bt.json"), "r") as f:
                    data = json.load(f)
                    f.close()
                self.wfile.write(json.dumps(data).encode())
                return
            else:
                # Save BT
                text = self.rfile.read(content_length).decode('-utf-8')
                with open(os.path.join(os.path.dirname(__file__), "bt.json"), "w") as f:
                    json.dump(json.loads(text), f, indent=4)
                    f.close()
                self.send_response(200)
                self.end_headers()

    def do_GET(self):
        if self.path == '/list':
            files = [filename for filename in os.listdir('uploads') if ".py" in filename]
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write('\n'.join(files).encode())
        elif self.path == "/stop":
            print(self.server.proc)
            self.server.proc.send_signal(signal.SIGINT)

            self.send_response(200)
            self.send_header('Location', '/')
            self.end_headers()
        elif self.path.startswith('/load/'):
            filename = self.path[6:]
            if not filename: return
            with open(os.path.join('uploads', filename), 'r') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(content.encode())
        elif self.path.startswith('/new'):
            new_filename = f'new-file-{random_string(6)}.py'
            with open(os.path.join('uploads', new_filename), 'w') as f:
                f.close()
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(new_filename.encode())
        elif self.path.startswith('/archive/'):
            filename = self.path[8:]
            if not filename: return
            if filename[0] == "/": filename = filename[1:]
            filepath = os.path.join('uploads', filename)
                
            if not os.path.exists("uploads/archive"):
                os.makedirs("uploads/archive")

            shutil.move(filepath, "uploads/archive")
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
        else:
            super().do_GET()

Handler = CustomHandler

server = None
def start_server():
    global server

    server = CustomServer(("", PORT), Handler)
    print(f"Serving at port {PORT}.")
    server.serve_forever()

python_exec = "env/bin/python"
glob_proc = None
ran_once = False
execute_filename = None
async def execute_script_thread(websocket, filename):
    global glob_proc, ran_once
    args = [python_exec, "-u", filename]
    glob_proc = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for line in glob_proc.stdout:
        print(line)
        await websocket.send(line.decode())
        time.sleep(0.001)

    # Process terminated/ended on its own
    e = subprocess.Popen([python_exec, "-u", "utils/stop_motors.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    await websocket.send("SCRIPT_ENDED_SIGNAL")
    if glob_proc: glob_proc.terminate()
    glob_proc = None
    ran_once = False

def toggle_process(filename):
    global ran_once, glob_proc, execute_filename
    if not ran_once:
        # Running
        execute_filename = filename
        ran_once = True
        return "SCRIPT_START_SIGNAL"
    else:
        # Stopping
        if glob_proc: glob_proc.terminate()
        glob_proc = None
        ran_once = False
        e = subprocess.Popen([python_exec, "-u", "utils/stop_motors.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return "SCRIPT_ENDED_SIGNAL"

async def websocket_handler(websocket: websockets.ServerConnection):
    try:
        print("e")
        if type(websocket) == websockets.server.WebSocketServerProtocol:
            filename = websocket.path[1:]
        else:
            filename = websocket.request.path[1:]
        await execute_script_thread(websocket, os.path.join('uploads', execute_filename))
    except websockets.exceptions.ConnectionClosedOK:
        pass

async def start_websocket_process():
    server = await websockets.serve(websocket_handler, "0.0.0.0", 8765)
    await server.wait_closed()

def start_websocket():
    asyncio.run(start_websocket_process())

if __name__ == "__main__":
    try:
        threads = [
            Thread(target=start_websocket),
            Thread(target=start_server)
        ]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

    except KeyboardInterrupt:
        if server:
            print("Shutting down server..")
            server.shutdown()
            server.server_close()
        print("Exiting..")
        sys.exit(0)
