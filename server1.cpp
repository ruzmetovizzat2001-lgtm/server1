#include <winsock2.h>
#include <windows.h>
#include <iostream>
#include <string>
#include <sstream>
#include <vector>
#include <mutex>

#pragma comment(lib, "ws2_32.lib")

std::mutex data_mutex;

// Oxirgi kelgan ma'lumotlar (yagona obyekt)
std::string lastJsonData = R"({ "status": "no data yet" })";

// POST JSON ma'lumotni olish
std::string extractPostData(const std::string& request) {
    size_t pos = request.find("\r\n\r\n");
    if (pos != std::string::npos) {
        return request.substr(pos + 4);
    }
    return "";
}

void handleClient(SOCKET client_socket) {
    char buffer[2048];
    int recv_size = recv(client_socket, buffer, sizeof(buffer) - 1, 0);
    if (recv_size == SOCKET_ERROR) {
        closesocket(client_socket);
        return;
    }

    buffer[recv_size] = '\0';
    std::string request(buffer);

    std::string response_body;
    std::string status = "200 OK";

    if (request.find("POST /upload") != std::string::npos) {
        std::string json = extractPostData(request);

        {
            std::lock_guard<std::mutex> lock(data_mutex);
            lastJsonData = json;
        }

        response_body = R"({"status": "received"})";

    } else if (request.find("GET /data") != std::string::npos) {
        {
            std::lock_guard<std::mutex> lock(data_mutex);
            response_body = lastJsonData;
        }
    } else {
        status = "404 Not Found";
        response_body = R"({"error": "invalid endpoint"})";
    }

    std::ostringstream response;
    response << "HTTP/1.1 " << status << "\r\n"
             << "Content-Type: application/json\r\n"
             << "Access-Control-Allow-Origin: *\r\n"
             << "Content-Length: " << response_body.size() << "\r\n"
             << "Connection: close\r\n\r\n"
             << response_body;

    send(client_socket, response.str().c_str(), response.str().size(), 0);
    closesocket(client_socket);
}

int main() {
    WSADATA wsa;
    SOCKET server_socket, client_socket;
    struct sockaddr_in server, client;
    int c;

    WSAStartup(MAKEWORD(2, 2), &wsa);
    server_socket = socket(AF_INET, SOCK_STREAM, 0);

    server.sin_family = AF_INET;
    server.sin_addr.s_addr = INADDR_ANY; // Agar global IP bo‘lsa, shuni qo‘ying
    server.sin_port = htons(8080); // Ehtimol bu portni routerning port forwardingida ochishingiz kerak bo‘ladi

    bind(server_socket, (struct sockaddr*)&server, sizeof(server));
    listen(server_socket, 5);

    std::cout << "Server ishga tushdi. Port: 8080\n";

    c = sizeof(struct sockaddr_in);

    while (true) {
        client_socket = accept(server_socket, (struct sockaddr*)&client, &c);
        if (client_socket != INVALID_SOCKET) {
            CreateThread(nullptr, 0, (LPTHREAD_START_ROUTINE)handleClient, (LPVOID)client_socket, 0, nullptr);
        }
    }

    closesocket(server_socket);
    WSACleanup();
    return 0;
}
