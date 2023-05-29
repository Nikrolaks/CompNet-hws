import time
import psutil

SPACE = 20

# я не верю, что может быть трафик терабайт в секунду и больше
# и да, можно было бинпоиском нормально написать, но тут блин только четыре режима...
def dgts(speed):
    if speed < 10:
        return 0
    elif speed < 100:
        return 1
    elif speed < 1000:
        return 2
    else:
        return 3
    
def shrink(speed, atch=""):
    if speed < 1024:
        mode = "B"
    elif speed < 1024 ** 2:
        mode = "K"
        speed /= 1024 
    elif speed < 1024 ** 3:
        mode = "B"
        speed /= 1024 ** 2
    else:
        mode = "G"
        speed /= 1024 ** 3

    return f"{speed:.2f}{mode}" + atch + " " * (SPACE - dgts(speed))

def one_print(cur, sent, recv, ssent, srecv):
    return " " * 150 + "\r" + \
        shrink(cur.bytes_recv - srecv) + \
        shrink(cur.bytes_sent - ssent) + \
        shrink(cur.bytes_recv - recv, "/s") + \
        shrink(cur.bytes_sent - sent, "/s")

if __name__ == "__main__":
    try:
        start = psutil.net_io_counters()
        bytes_sent = start.bytes_sent
        bytes_recv = start.bytes_recv
        start_download, start_upload = start.bytes_recv, start.bytes_sent

        # тут был подгон значений...
        print(
            "Total loaded" + " " * (SPACE - 11 + 4) + \
            "Total uploaded" + " " * (SPACE - 13 + 4) + \
            "Loading speed" + " " * (SPACE - 10 + 4) + \
            "Uploading speed")

        laststr = ""
        while True:
            cur = psutil.net_io_counters()

            laststr = one_print(cur, bytes_sent, bytes_recv, start_upload, start_download)
            
            print(laststr, end="\r")

            bytes_sent, bytes_recv = cur.bytes_sent, cur.bytes_recv
            time.sleep(1)

    except KeyboardInterrupt:
        print(laststr)
