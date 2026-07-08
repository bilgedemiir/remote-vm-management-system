import socket
import json
import sys
import os
import threading

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database.repositories.client_repository import (
    register_or_update_client,
    set_client_offline
)

HOST = "0.0.0.0"
PORT = 9000

def handle_client(client_socket, client_address):
    hostname = None

    try:
        print(f"Agent bağlandı: {client_address}")

        message = client_socket.recv(1024).decode("utf-8")
        client_data = json.loads(message)

        if client_data["type"] == "register":
            hostname = client_data["hostname"]

            register_or_update_client(
                client_data["hostname"],
                client_data["ip_address"],
                client_data["operating_system"]
            )

            print(f"Client kaydedildi/güncellendi: {hostname}")

        while True:
            data = client_socket.recv(1024)

            if not data:
                break

    except Exception as error:
        print(f"Client bağlantısında hata oluştu: {error}")

    finally:
        if hostname:
            set_client_offline(hostname)
            print(f"Client offline yapıldı: {hostname}")

        client_socket.close()

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_socket.bind((HOST, PORT))
    server_socket.listen()

    print(f"Socket Server çalışıyor: {HOST}:{PORT}")
    print("Agent bağlantısı bekleniyor...")

    while True:
        client_socket, client_address = server_socket.accept()

        client_thread = threading.Thread(
            target=handle_client,
            args=(client_socket, client_address)
        )

        client_thread.start()




if __name__ == "__main__":
    start_server()