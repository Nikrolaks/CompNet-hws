import argparse
import socket
from units import LOG, Sender, Reciever

HOST = "127.0.0.1"
PORT = 8789

parser = argparse.ArgumentParser("HW 9 Server Kopeikina Sofya")
parser.add_argument("timeout", type=int)
parser.add_argument("listen_ttl", type=int)
args = parser.parse_args()

def server():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as serv:
            serv.bind((HOST, PORT))
            reciever = Reciever(serv, args.listen_ttl)
            reciever.recieve("server_recieved.png")
            if reciever.addr:
                sender = Sender(serv, args.timeout, reciever.addr)
                sender.send("banana.png")
    except KeyboardInterrupt:
        LOG("Server", "INFO", f"Stopping server")
    except Exception as err:
        LOG("Server", "ERROR", f"Catched error: {err}")


if __name__ == "__main__":
    LOG("Oracle", "INFO", "Starting server")
    server()
