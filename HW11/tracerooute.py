import socket
import struct
import time
import sys

class TraceRoouter:
    def extract_code(self, data):
        res = struct.unpack("!BB", data[20:22])
        return res[0], res[1]
    # 1 - тип (8), байт, B
    # 2 - код (0), байт, B
    # 3 - контрольная сумма, 2 байта, H
    # 4 - идентификатор, 2 байта, H
    # 5 - Номер последовательности, 2 байта, H
    PACKAGE_FORMAT = "!BBHHH"

    def __generate_pckg(self):
        def calc_checksum(data):
            checksum = 0
            for i in range(0, 8, 2):
                checksum += struct.unpack("!H", data[i : i + 2])[0]
            
            checksum = (checksum >> 16) + (checksum & 0xFFFF)
            checksum += (checksum >> 16)
            checksum = ~checksum & 0xFFFF

            return checksum

        pckg_n = 0
        while True:
            pckg_n += 1
            unverified_pckg = struct.pack(self.PACKAGE_FORMAT, 8, 0, 0, 1, pckg_n)
            checksum = calc_checksum(unverified_pckg)

            yield struct.pack(self.PACKAGE_FORMAT, 8, 0, checksum, 1, pckg_n)

    def __init__(self, dst, pckg_count=3):
        self.dst = (socket.gethostbyname(dst), 33434)
        self.pckg_count = pckg_count
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
        self.conn.settimeout(2)

    def __ping(self, pckg, ttl):
        self.conn.setsockopt(socket.IPPROTO_IP, socket.IP_TTL, ttl)
        try:
            self.conn.sendto(pckg, self.dst)

            begin = time.time()
            data, addr = self.conn.recvfrom(1024)
            end = time.time()

            rtt = (end - begin) * 1000

            return (addr[0], rtt, data)
        except socket.timeout:
            return None
    
    def trace(self):
        print(f"Трассировка до {self.dst[0]}")
        ttl = 1
        cur_ping = 0
        cur_ip = None
        cur_rtt = "*"
        should_stop = False
        print(f"{ttl})", end="\t")

        for pckg in self.__generate_pckg():
            res = self.__ping(pckg, ttl)
            if res is not None:
                cur_ip, cur_rtt, data = res

                cur_rtt = "{:4.2f}".format(cur_rtt)
                type, code = self.extract_code(data)
                should_stop = should_stop or ((type == 0 and code == 0) or (type == 3 and code == 3))
                if not should_stop and (type != 11 or code != 0):
                    raise RuntimeError("Tracerooute recieve strange reply")
            
            print(f"{cur_rtt}", end="\t")

            cur_ping += 1
            cur_rtt = "*"
            if cur_ping >= self.pckg_count:
                if cur_ip is None:
                    print("Превышено время ожидания")
                else:
                    try:
                        name = socket.gethostbyaddr(cur_ip)
                        print(f"{name[0]} [{cur_ip}]")
                    except socket.herror:
                        print(f"{cur_ip}")

                cur_ping = 0
                cur_ip = None
                ttl += 1
                if should_stop:
                    break
                print(f"{ttl})", end="\t")
        
        self.conn.close()
        print("Трассировка завершена")

if __name__ == "__main__":
    tracerooute = TraceRoouter(sys.argv[1], int(sys.argv[2]))
    tracerooute.trace()