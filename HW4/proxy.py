import argparse
import socket
import re
import os
import datetime

HOST = "127.0.0.1"

parser = argparse.ArgumentParser(prog='CompNet HW 4 Kopeikina Sofya')
parser.add_argument('port', type=int)
parser.add_argument('logfilepath', type=str)
parser.add_argument('blacklist', type=str)
args = parser.parse_args()

PORT = args.port
LOGGER_PATH = args.logfilepath
LOG = None
BLACKLIST = None
CACHE_FOLDER = "cache"
DTIME_FORMAT = r"%a, %d %b %Y %H:%M:%S GMT"
LM_HEADER = "Last-Modified: "
ETAG_HEADER = "Etag: "

CACHED = {}

CACHE_200_RESPONSE = "HTTP/1.1 200 OK\r\n\r\n".encode()
CODE_400_RESPONSE = "HTTP/1.1 400 Bad request\r\n\r\n".encode()
CODE_423_RESPONSE = "HTTP/1.1 423 Locked\r\n\r\n".encode()

REQUEST_FORMAT = "{method} /{endpoint} HTTP/1.1\r\n"
GET_CACHE_FORMAT = 'GET /{endpoint} HTTP/1.1\r\nHost: {host}\r\nIf-Modified-Since: {ims}\r\nIf-None-Match: "{etag}"\r\n\r\n'

def error_handler(error_code):
    print(f"[LOG] Proxer: response with error: {error_code}")

def save_to_cache(url:str, obj: bytes, last_modified: str, etag: str):
    with open(CACHE_FOLDER + f"/{etag}.cache", "wb") as f:
        print(f"[LOG] my_нжинкс: cached object with etag {etag} from url: {url}")
        f.write(obj)
        CACHED[url] = (etag, last_modified)

def main_proxer_action(proxer, request):
    try:
        proxer.send(request)
        dataFull = b""
        while True:
            data = proxer.recv(1024)
            dataFull = dataFull + data
            if len(data) < 1024:
                break
        print("[LOG] Proxer: recieved response")
        if len(dataFull) == 0:
            print(f"[ERROR] Proxer: empty response")
            return CODE_400_RESPONSE, 400
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

def load_from_cache(etag:str):
    with open(CACHE_FOLDER + f"/{etag}.cache", "rb") as content:
        return content.read()

def ask_cache(conn, host, endpoint):
    url = host + "/" + endpoint
    if url not in CACHED:
        res, respcode = main_proxer_action(
            conn,
            (
                REQUEST_FORMAT.format(method="GET", endpoint=endpoint) +
                f"Host: {host}\r\n\r\n"
            ).encode()
        )
        body_begin = res.find(b"\r\n\r\n")
        body = res[body_begin + 4:]
        if body_begin == -1 or len(body) == 0:
            return False, res, respcode

        lm_begin = res.find(b'Last-Modified: ')
        etag_begin = res.find(b'Etag: ')

        if lm_begin == -1 or etag_begin == -1:
            print("[LOG] my_нжинкс: no enough information for caching")
            return False, res, respcode

        lm_end = res[lm_begin:].find(b'\r\n')
        etag_end = res[etag_begin:].find(b'\r\n')

        lm = res[lm_begin : ][len(LM_HEADER) : lm_end].decode()
        etag = res[etag_begin:][len(ETAG_HEADER) + 1 : etag_end - 1].decode() # убираю еще кавычки

        print(f"[LOG] my_нжинкс: recieve information: etag: {etag}, last-modified: {lm}")
        save_to_cache(url, body, lm, etag)
        return True, res, respcode
    else:
        print("[LOG] my_нжинкс: asking for information about object modification")
        info = CACHED[url]
        res, respcode = main_proxer_action(
            conn,
            GET_CACHE_FORMAT.format(
                endpoint=endpoint,
                host=host,
                ims=info[1],
                etag=info[0]
            ).encode()
        )
        if respcode == 304:
            print(f"[LOG] my_нжинкс: not modified, returning cached")
            return False, CACHE_200_RESPONSE + load_from_cache(info[0]), 200
        else:
            print("[LOG] my_нжинкс: object modified or протух, loading")
            del CACHED[url]
            return ask_cache(conn, host, endpoint)


def redirecting_service(method: str, host: str, endpoint: str, httptail: bytes):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as proxer:
            print("[LOG] Proxer: trying to connect to host")
            proxer.connect((host, 80)) # несмотря на то, что вы советовали мне подключаться к дефолтному, это блин вообще не работает, 
                                       # а в том примере, который дали, совершенно другой порт, так что юзаю его
            print("[LOG] Proxer: connected to host")
            if method == "POST":
                return main_proxer_action(
                    proxer,
                    REQUEST_FORMAT(method=method, endpoint=endpoint).encode() + httptail
                )
            else:
                ismodified, resp, respcode = ask_cache(proxer, host, endpoint)
                return resp, respcode # пока не придумала, куда деть информацию о том, обновился ли кэш
    except Exception as err:
        print(f"[ERROR] Proxer: catch some error: {err}")
        return CODE_400_RESPONSE, 400

def replace_host(request, newhost):
    host_begin = request.find(b'Host: ')
    if host_begin != -1:
        host_end = request[host_begin:].find(b'\r\n')
        return request[:host_begin] + f"Host: {newhost}".encode() + request[host_end:]
    else:
        return f"Host: {newhost}\r\n".encode() + request

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
                    getmatch = re.match('.*GET /(.*) HTTP.*', request)
                    postmatch = re.match('.*POST /(.*) HTTP.*', request)
                    if getmatch or postmatch:
                        if getmatch:
                            print(f"[LOG] Proxy: redirecting GET request")
                            urlmatch = getmatch.group(1)
                            method = "GET"
                        else:
                            print(f"[LOG] Proxy: redirecting POST request")
                            urlmatch = postmatch.group(1)
                            method = "POST"

                        host_end = urlmatch.find('/')
                        host = urlmatch
                        request = ""
                        if host_end != -1:
                            host = urlmatch[:host_end]
                            request = urlmatch[host_end + 1:]
                        
                        if host in BLACKLIST:
                            print(f"[LOG] Proxy: request from host in blacklist: {host}")
                            conn.send(CODE_423_RESPONSE)
                            continue

                        toreturn, code = \
                            redirecting_service(
                                method,
                                host,
                                request,
                                replace_host(dataFull[request_end + 1:], host)
                        )
                        print(f"URL: {urlmatch} CODE: {code}", file=LOG)
                        conn.send(toreturn)
                    else:
                        print(f"[LOG] Proxy: unavialable type of request")
                        conn.send(CODE_400_RESPONSE)

    except KeyboardInterrupt:
        print("[INFO] Stopping server")

if __name__ == "__main__":
    if not os.path.exists(CACHE_FOLDER):
        os.mkdir(CACHE_FOLDER)
    with open(args.blacklist, "r") as config:
        hosts = config.read().split('\n')
        BLACKLIST = set(hosts)
    LOG = open(LOGGER_PATH, "w")
    proxy_server()
    LOG.close()
