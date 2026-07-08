import socket
import json
import platform
import time

HOST = "192.168.80.1"
PORT = 9000

def start_agent():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print("Socket Server'a bağlanılıyor...")

    client_socket.connect((HOST, PORT))

    print("Bağlantı başarılı.")

    hostname = socket.gethostname()

    ip_address = socket.gethostbyname(hostname)

    operating_system = platform.system()

    #print(hostname)
    #print(ip_address)
    #print(operating_system)

    #message = "Merhaba Sunucu"

    client_info = {
        'type': 'register',
        'hostname': hostname,
        'ip_address': ip_address,
        'operating_system': operating_system
    }

    message=json.dumps(client_info)

    client_socket.send(message.encode("utf-8"))

    print("Mesaj gönderildi.")

    while True:
        time.sleep(1)

    client_socket.close()

    print("Bağlantı kapatıldı.")


if __name__ == "__main__":
    start_agent()
