import argparse
import socket
import re

parser = argparse.ArgumentParser(prog='CompNet HW 3 Kopeikina Sofya Client')
parser.add_argument('host', type=str)
parser.add_argument('port', type=int)
parser.add_argument('filename', type=str)

args = parser.parse_args()

request = \
"GET /{filename} HTTP/1.1\n\
Host: {host}:{port}\n\
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8, application/signed-exchange;v=b3;q=0.9\n\
Accept-Language: ru,en;q=0.9"

idx = 2

port = args.port

while idx:
    idx -= 1
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.connect((args.host, port))
        client.sendall(request.format(
            filename=args.filename,
            host=args.host,
            port=port
        ).encode())
        dataFull = b''
        while True:
            data = client.recv(1024)
            dataFull = dataFull + data
            if len(data) < 1024:
                break
        if idx:
            data = dataFull.decode("utf-8")
            print(data)
        else:
            headers_end = dataFull.find(b'\n\n')
            data = dataFull[:headers_end + 2].decode("utf-8")
            print(data)
            print(dataFull[headers_end+2:])
        print()
        if data.splitlines()[0] == "HTTP/1.1 200 OK":
            exit()
        else:
            strport = str(re.search(f"Location: http://{args.host}:(.*)/{args.filename}", data).group(1))
            port = int(strport)