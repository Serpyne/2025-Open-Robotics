#
# Worker script runs on start-up
# Runs the separate pipeline to control the main script
# Allows users to upload and run scripts on the robot (without restarting the PI)
#

import http.server
import socketserver
import os
import sys
import cgi
import subprocess
import random
from threading import Thread
from string import ascii_letters
from typing import TextIO

PORT = 8000
TEST_STREAM = TextIO()

def test_thread(args):
    global process_thread
    def process():
        subprocess.run(args,
                    # capture_output=True, text=True,
                    stderr=sys.stderr, stdout=sys.stdout)
    process_thread = Thread(target=process)
    process_thread.start()

    name = random_string(2)
    i = 0
    while process_thread is not None:
        print(name, i)
        i += 1

def random_string(count):
    return "".join([random.choice(ascii_letters) for i in range(count)])

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
            
            worker_thread = Thread(target=test_thread, args=(['python', os.path.join('uploads', filename)],))
            process_thread = None
            worker_thread.start()
            
            self.send_response(200)
            self.end_headers()

    def do_GET(self):
        if self.path == '/list':
            files = os.listdir('uploads')
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write('\n'.join(files).encode())
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
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving at port {PORT}.")
        httpd.serve_forever()

main_thread = Thread(target=main)
main_thread.start()
worker_thread = None
process_thread = None