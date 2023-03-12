from threading import Thread
from queue import Queue
import argparse
import time
import socket
import re
import os

HOST = "127.0.0.1"
PORT = 7070

parser = argparse.ArgumentParser(prog='CompNet HW 3 Kopeikina Sofya Server')
parser.add_argument('concurrencyLevel', type=int)
concurrencyLevel = parser.parse_args().concurrencyLevel

available_ports = Queue()

count_of_ports = min(concurrencyLevel, PORT - 6060)

threads_sockets = {}

for port in range(6060, 6060 + count_of_ports):
    available_ports.put(port)
    threads_sockets[port] = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    threads_sockets[port].bind((HOST, port))
    threads_sockets[port].listen()

def make_responser(port):
    RESPONSER_PORT = port
    def responser():
        global available_ports
        s = threads_sockets[RESPONSER_PORT]
        print(f"[LOG] Responser listening port {RESPONSER_PORT}")
        conn, addr = s.accept()
        with conn:
            time.sleep(10) # for testing
            print(f"[LOG] Responser({RESPONSER_PORT}): connected by {addr}")
            dataFull = b''
            while True:
                data = conn.recv(1024)
                dataFull = dataFull + data
                if len(data) < 1024:
                    break
            print(f"[LOG] Responser({RESPONSER_PORT}): recieved {len(dataFull)} bytes of data")
            request = dataFull.decode("utf-8")
            print(request)
            filematch = re.match('.*GET /(.*) HTTP.*', request)
            filename = ""
            if filematch:
                filename = str(filematch.group(1))
            if not os.path.exists(filename):
                print(f"[WARN] Responser({RESPONSER_PORT}): Required ({filename}) file isn't exist")
                conn.send(f"HTTP/1.1 404 Not Found".encode())
            else:
                print(f"[LOG] Responser({RESPONSER_PORT}): Sending required ({filename}) file")
                with open(filename, 'rb') as requestedFile:
                    fileEntry = requestedFile.read()
                    response = f"HTTP/1.1 200 OK\n\n".encode()
                    conn.send(response + fileEntry)
        print(f"[LOG] Responser({RESPONSER_PORT}): done")
        available_ports.put(RESPONSER_PORT)
    return responser

def processer():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as processer:
            processer.bind((HOST, PORT))
            processer.listen(1000) # вот тут очередь
            while True:
                conn, addr = processer.accept()
                with conn:
                    print(f"[LOG] Processer: connected by {addr}")
                    dataFull = b''
                    while True:
                        data = conn.recv(1024)
                        dataFull = dataFull + data
                        if len(data) < 1024:
                            break
                    print(f"[LOG] Processer: recieved {len(dataFull)} bytes of data")
                    request = dataFull.decode("utf-8")
                    filematch = re.match('.*GET /(.*) HTTP.*', request)
                    filepath = ""
                    if filematch:
                        filepath = filematch.group(1)
                    print(f"[LOG] Processor: Check and wait while at least one thread becomes free")
                    while available_ports.empty():
                        pass
                    responsePort = available_ports.get()
                    responseThread = Thread(target=make_responser(responsePort))
                    responseThread.start()
                    print(f"[LOG] Processer: send redirect response")
                    conn.send(f"HTTP/1.1 307 Temporary Redirect\nLocation: http://{HOST}:{responsePort}/{filepath}".encode())
    except KeyboardInterrupt:
        print("[INFO] Stopping server")

mainThread = Thread(target=processer())

mainThread.start()
mainThread.join()

for port in threads_sockets:
    threads_sockets[port].close()
print("[INFO] Exiting programm")