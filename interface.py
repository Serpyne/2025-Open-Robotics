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
from threading import Thread
from string import ascii_letters
from typing import TextIO

PORT = 8000
TEST_STREAM = TextIO()

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
        elif self.path == '/execute':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            filename = post_data

            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.send_header('Transfer-Encoding', 'chunked')
            self.end_headers()

            async def start_process():
                args = ["python", "-u", os.path.join("uploads", filename)]
                with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True) as proc:
                    self.server.proc = proc
                    for line in proc.stdout:
                        # print(proc)
                        self.wfile.write(line.encode())
                        self.wfile.flush()
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            result = new_loop.run_until_complete(start_process())

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
        elif self.path.startswith('/new/'):
            filename = self.path[5:]
            # if not filename: return
            with open(os.path.join('uploads', 'new-file-'+random_string(6)), 'w') as f:
                f.close()
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
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

def main():
    with CustomServer(("", PORT), Handler) as httpd:
        print(f"Serving at port {PORT}.")
        httpd.serve_forever()

if __name__ == "__main__":
    Thread(target=main).start()