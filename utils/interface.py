#
# Worker script runs on start-up
# Runs the separate pipeline to control the main script
# Allows users to upload and run scripts on the robot (without restarting the PI)
#

import http.server
import socketserver
import os
import cgi
import signal
import subprocess
import random
import asyncio
import websockets
from threading import Thread
from string import ascii_letters
from typing import TextIO

PORT = 8000

def random_string(count):
    return "".join([random.choice(ascii_letters) for i in range(count)])

class CustomServer(socketserver.TCPServer):
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

    def do_GET(self):
        if self.path == '/list':
            files = os.listdir('uploads')
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
        elif self.path.startswith('/delete/'):
            filename = self.path[8:]
            if not filename: return
            filepath = os.path.join('uploads', filename)
            if os.path.exists(filepath):
                os.remove(filepath)
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
        else:
            super().do_GET()

Handler = CustomHandler

def start_server():
    with CustomServer(("", PORT), Handler) as httpd:
        print(f"Serving at port {PORT}.")
        httpd.serve_forever()

glob_proc = None
ran_once = False
async def execute_script_thread(filename):
    global glob_proc
    args = ["python", "-u", filename]
    with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as proc:
        glob_proc = proc
        for line in proc.stdout:
            yield line
            await asyncio.sleep(0.0001)

async def websocket_handler(websocket: websockets.ServerConnection):
    global ran_once, glob_proc
    if not ran_once:
        print("Running")
        ran_once = True
    else:
        print("Stopping")
        await websocket.send("SCRIPT_ENDED_SIGNAL")
        if glob_proc is None: glob_proc.terminate()
        glob_proc = None
        ran_once = False
        return
    
    try:
        filename = websocket.request.path[1:]
        async for line in execute_script_thread(os.path.join("uploads", filename)):
            await websocket.send(line.decode())
        # Process terminated/ended on its own
        await websocket.send("SCRIPT_ENDED_SIGNAL")
        if glob_proc: glob_proc.terminate()
        glob_proc = None
        ran_once = False
        print("Ended")
    except websockets.exceptions.ConnectionClosedOK:
        pass

async def start_websocket_process():
    server = await websockets.serve(websocket_handler, "127.0.0.1", 8765)
    await server.wait_closed()
def start_websocket():
    asyncio.run(start_websocket_process())

if __name__ == "__main__":
    Thread(target=start_websocket).start()
    Thread(target=start_server).start()