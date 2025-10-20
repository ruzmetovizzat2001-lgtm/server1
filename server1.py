from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import threading

# Global o'zgaruvchi (oxirgi kelgan JSON)
latest_data = {
    "status": "no data yet"
}
data_lock = threading.Lock()

class CarTrackerHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def do_OPTIONS(self):
        # CORS uchun
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        if self.path == "/data":
            with data_lock:
                response = json.dumps(latest_data)
            self._set_headers()
            self.wfile.write(response.encode('utf-8'))
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        if self.path == "/upload":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data)
                with data_lock:
                    global latest_data
                    latest_data = data
                self._set_headers()
                self.wfile.write(json.dumps({"status": "received"}).encode('utf-8'))
            except json.JSONDecodeError:
                self.send_error(400, "Invalid JSON")
        else:
            self.send_error(404, "Not Found")


def run(server_class=HTTPServer, handler_class=CarTrackerHandler, port=8080):
    server_address = ('', port)  # '' => har qanday IP-dan qabul qiladi (global)
    httpd = server_class(server_address, handler_class)
    print(f"Server ishga tushdi. Port: {port}")
    httpd.serve_forever()


if __name__ == "__main__":
    run()
