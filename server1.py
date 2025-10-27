import json
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import ssl

# Global o'zgaruvchi
latest_data = {"status": "no data yet"}
data_lock = threading.Lock()

# ==========================
#   HTTPS JSON server qismi
# ==========================
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

def run_https_server(port=8443):
    server_address = ('', port)
    httpd = HTTPServer(server_address, CarTrackerHandler)

    # SSL (sertifikat kerak)
    # Sertifikatlarni quyidagicha yarating:
    # openssl req -new -x509 -keyout server.pem -out server.pem -days 365 -nodes
    httpd.socket = ssl.wrap_socket(
        httpd.socket,
        server_side=True,
        certfile="server.pem",
        ssl_version=ssl.PROTOCOL_TLS
    )

    print(f"✅ HTTPS server ishga tushdi: https://localhost:{port}/data")
    httpd.serve_forever()

# ==========================
#   TCP qismi (ma’lumot qabul qiladi)
# ==========================
def run_tcp_server(host='0.0.0.0', port=9000):
    global latest_data
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen(5)
        print(f"📡 TCP server ishga tushdi: {host}:{port}")

        while True:
            conn, addr = server_socket.accept()
            with conn:
                print(f"🟢 Yangi TCP ulanish: {addr}")
                data = conn.recv(4096)
                if not data:
                    continue
                try:
                    json_data = json.loads(data.decode('utf-8'))
                    with data_lock:
                        latest_data = json_data
                    print("📩 Ma’lumot qabul qilindi:", json_data)
                    conn.sendall(b'{"status": "received"}')
                except json.JSONDecodeError:
                    print("⚠️ Noto‘g‘ri JSON!")
                    conn.sendall(b'{"error": "invalid json"}')

# ==========================
#   Asosiy ishga tushirish
# ==========================
if __name__ == "__main__":
    # HTTPS serverni alohida threadda ishlatamiz
    https_thread = threading.Thread(target=run_https_server, daemon=True)
    https_thread.start()

    # TCP serverni ishga tushiramiz
    run_tcp_server()
