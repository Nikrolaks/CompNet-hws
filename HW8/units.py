import socket
import datetime
import signal
import scipy.stats as ss # yes, bruteforce а что

PCKG_SIZE = 1024 + 20 # а-ля заголовок
VERBOSITY = True

def LOG(src: str, lvl: str, msg: str):
    if VERBOSITY:
        time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{lvl}] {time} {src}: {msg}")

class Package:
    def __init__(self, n: int = 0):
        self.n = n
        self.idx = 0
    
    def load_data(self, data: bytes):
        self.data = data
        return self
    
    def make_package(self) -> bytes:
        return f"{self.idx} {self.n}\n\n".encode() + self.data

    def lost(self):
        self.idx = self.idx ^ 1
        return self

    def decode_package(self, package: bytes):
        delimiter = package.find(b"\n\n")
        self.idx, self.n = map(int, package[:delimiter].decode().split())
        self.data = package[delimiter + 2:]
        return self


class Ack:
    def __init__(self, ackn: int = 0, n: int = 0):
        self.ackn = ackn
        self.n = n

    def load_data(self, pckg: Package):
        self.ackn = pckg.idx
        self.n = pckg.n
        return self

    def check_ack(self, ackn: int, n: int):
        LOG("ACK", "INFO", f"{ackn} {n} || {self.ackn} {self.n}")
        return self.ackn == ackn and self.n == n

    def make_package(self) -> bytes:
        return f"{self.ackn} {self.n}".encode()

    def decode_package(self, package: bytes):
        self.ackn, self.n = map(int, package.split())
        return self


class Sender:
    def __init__(self, sock: socket.socket, timeout: int, dst):
        self.conn = sock
        self.package_size = 1024
        self.timeout = timeout
        self.dst = dst

    def wait_ack(self, ackn: int, n: int):
        while True:
            dataFull = b""
            data, addr = self.conn.recvfrom(PCKG_SIZE)
            dataFull = dataFull + data
            ack = Ack().decode_package(dataFull)
            if ack.check_ack(ackn, n):
                break
        

    def pckg_delivered(self, ackn: int, n: int):
        class Timeout(Exception):
            pass

        def handler(signum, stack):
            LOG("Sender", "INFO", "It looks like package hasn't been delivered")
            raise Timeout
        
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(self.timeout)
        try:
            self.wait_ack(ackn, n)
        except Timeout:
            return False
        signal.alarm(0)
        return True

    def send_chunk(self, n: int, chunk: bytes):
        pckg = Package(n).load_data(chunk)
        while True:
            # n+1/all, только потому что я не знаю как на английском сказать посылаю "итый" пакет
            # а количество всех передавать или хранить вломак
            LOG("Sender", "INFO", f"Sending {n + 1}/all package with idx {pckg.idx}")
            self.conn.sendto(pckg.make_package(), self.dst)
            if self.pckg_delivered(pckg.idx, pckg.n):
                return
            else:
                pckg.lost()

    def send(self, filepath: str):
        with open(filepath, "rb") as file:
            data = file.read()
            LOG("Sender", "INFO", "Opened file")
            chunks = [data[i : i+self.package_size] for i in range(0, len(data), self.package_size)]
            LOG("Sender", "INFO", f"Plan to send {len(chunks)} packages")
            for n, chunk in enumerate(chunks):
                self.send_chunk(n, chunk)


class Reciever:
    def __init__(self, sock: socket.socket, timeout: int):
        self.conn = sock
        self.last_recieved = -1
        self.data = b""
        self.timeout = timeout
        self.thief = ss.bernoulli(0.3)
    
    def send_ack(self, pckg: Package):
        if not self.thief.rvs(size=1)[0]:
            ack = Ack().load_data(pckg)
            LOG("Reciever", "INFO", f"Sending ack ({ack.ackn} {ack.n}) response")
            self.conn.sendto(ack.make_package(), self.addr)
        else:
            LOG("Thief", "INFO", "Stole the package")
    
    def recieve_pckg(self):
        class Timeout(Exception):
            pass

        def handler(signum, stack):
            LOG("Reciever", "INFO", "End of transfer")
            raise Timeout
        
        data = b''
        signal.signal(signal.SIGALRM, handler)
        signal.alarm(self.timeout)
        try:
            data, self.addr = self.conn.recvfrom(PCKG_SIZE)
        except Timeout:
            return False
        signal.alarm(0)
        pckg = Package().decode_package(data)
        self.send_ack(pckg)
        if self.last_recieved < pckg.n:
            self.data = self.data + pckg.data
            self.last_recieved += 1
        return True

    def recieve(self, filepath: str):
        LOG("Reciever", "INFO", "Start to listen")
        while self.recieve_pckg():
            pass
        with open(filepath, "wb") as file:
            LOG("Reciever", "INFO", "Writing recieved data to file")
            file.write(self.data)
    
    def clear_data(self):
        self.data = b""

