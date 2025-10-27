import os
import json
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

# Global JSON ma'lumot
latest_data = {"status": "no data yet"}
data_lock = threading.Lock()

# Render tomonidan berilgan port
PORT_HTTP = int(os.getenv("PORT", 10000))
PORT_TCP = 9000  # TCP uchun lokal port (thread ichida)

# ---------------------
# HTTP server
# ---------------------
class CarTrackerHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def do_GET(self):
        if self.path == "/data":
            with data_lock:
                response = json.dumps(latest_data)
            self._set_headers()
            self.wfile.write(response.encode('utf-8'))
        else:
            self.send_error(404, "Not Found")

def run_http_server():
    server_address = ('0.0.0.0', PORT_HTTP)
    httpd = HTTPServer(server_address, CarTrackerHandler)
    print(f"🌍 HTTP server ishlayapti: 0.0.0.0:{PORT_HTTP}")
    httpd.serve_forever()

# ---------------------
# TCP server thread
# ---------------------
def run_tcp_server():
    global latest_data
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', PORT_TCP))  # 0.0.0.0 => hamma IPdan qabul qiladi
        s.listen(5)
        print(f"📡 TCP server ishlayapti: 0.0.0.0:{PORT_TCP}")
        while True:
            conn, addr = s.accept()
            with conn:
                print(f"🟢 TCP ulanish: {addr}")
                data = conn.recv(4096)
                if not data:
                    continue
                try:
                    json_data = json.loads(data.decode('utf-8'))
                    with data_lock:
                        latest_data = json_data
                    conn.sendall(b'{"status": "received"}')
                except json.JSONDecodeError:
                    conn.sendall(b'{"error": "invalid json"}')

# ---------------------
# Main
# ---------------------
if __name__ == "__main__":
    tcp_thread = threading.Thread(target=run_tcp_server, daemon=True)
    tcp_thread.start()
    run_http_server()
