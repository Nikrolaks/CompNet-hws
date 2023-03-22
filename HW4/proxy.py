from threading import Thread
from queue import Queue
import argparse
import time
import socket
import re
import os

HOST = "127.0.0.1"

parser = argparse.ArgumentParser(prog='CompNet HW 4 Kopeikina Sofya')
parser.add_argument('port', type=int)
parser.add_argument('logfilepath', type=str)
args = parser.parse_args()

PORT = args.port
LOGGER_PATH = args.logfilepath
LOG = None

CODE_400_RESPONSE = "HTTP/1.1 400 Bad request".encode()

REQUEST_FORMAT = "GET /{endpoint} HTTP/1.1\n"

def error_handler(error_code):
    print(f"[LOG] Proxer: response with error: {error_code}")

def redirecting_service(host: str, endpoint: str, httptail: bytes):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as proxer:
            print("[LOG] Proxer: trying to connect to host")
            proxer.connect((host, 5000))
            print("[LOG] Proxer: connected to host")
            proxer.sendall((REQUEST_FORMAT.format(endpoint=endpoint)).encode() + httptail)
            dataFull = b""
            while True:
                data = proxer.recv(1024)
                dataFull = dataFull + data
                if len(data) < 1024:
                    break
            print("[LOG] Proxer: recieved response")
            response_end = dataFull.find(b'\n')
            if response_end == -1:
                response_end = len(dataFull)
            data = dataFull[:response_end].decode("utf-8")
            body = dataFull[response_end + 1:]
            response_code = int(re.match("HTTP/\d\.\d (\d*) .*", data).group(1))
            if response_code >= 400:
                error_handler(response_code)
            return dataFull, response_code
    except Exception as err:
        print(f"[ERROR] Proxer: catch some error: {err}")
        return CODE_400_RESPONSE, 400

def proxy_server():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as processer:
            processer.bind((HOST, PORT))
            processer.listen(10)
            while True:
                conn, addr = processer.accept()
                with conn:
                    print(f"[LOG] Proxy: connected by {addr}")
                    dataFull = b''
                    while True:
                        data = conn.recv(1024)
                        dataFull = dataFull + data
                        if len(data) < 1024:
                            break
                    print(f"[LOG] Proxy: recieved {len(dataFull)} bytes of data")
                    request_end = dataFull.find(b'\n')
                    request = dataFull[:request_end].decode("utf-8")
                    filematch = re.match('.*GET /(.*) HTTP.*', request)
                    if filematch:
                        print(f"[LOG] Proxy: redirecting request")
                        urlmatch = filematch.group(1)
                        host_end = urlmatch.find('/')
                        host = urlmatch
                        request = ""
                        if host_end != -1:
                            host = urlmatch[:host_end]
                            request = urlmatch[host_end + 1:]
                        toreturn, code = \
                            redirecting_service(
                                host,
                                request,
                                dataFull[request_end + 1:]
                        )
                        print(f"URL: {urlmatch} CODE: {code}", file=LOG)
                        conn.send(toreturn)
                    else:
                        print(f"[LOG] Proxy: unavialable type of request")
                        conn.send(CODE_400_RESPONSE)

    except KeyboardInterrupt:
        print("[INFO] Stopping server")

if __name__ == "__main__":
    LOG = open(LOGGER_PATH, "w")
    proxy_server()
    LOG.close()
