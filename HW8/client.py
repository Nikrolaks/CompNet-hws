import argparse
import socket
import time
from units import LOG, Sender, Reciever

HOST = "127.0.0.1"
PORT = 8789

parser = argparse.ArgumentParser("HW 9 client Kopeikina Sofya")
parser.add_argument("timeout", type=int)
parser.add_argument("listen_ttl", type=int)
args = parser.parse_args()

def client():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as cl:
            sender = Sender(cl, args.timeout, (HOST, PORT))
            sender.send("tomato.png")
            time.sleep(args.listen_ttl + 5)
            reciever = Reciever(cl, args.listen_ttl)
            reciever.recieve("client_recieved.png")
    except KeyboardInterrupt:
        LOG("Client", "INFO", "Stopping client")
    except Exception as err:
        LOG("Client", "ERROR", f"Catched error: {err}")

if __name__ == "__main__":
    LOG("Oracle", "INFO", "Starting client")
    client()
