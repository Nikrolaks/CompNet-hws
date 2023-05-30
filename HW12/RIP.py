import json
from queue import Queue
from copy import deepcopy
from collections import defaultdict
import os

class RIPEntry:
    def __init__(self, next_hop=0, metric=16):
        self.next_hop = next_hop
        self.metric = metric

class RIP:
    PRINT_FMT = "{:<22}{:<22}{:<22}{:<22}\r\n"
    def __init__(self, as_fpath):
        with open(as_fpath, "r") as as_file:
            self.autoS = json.loads(as_file.read())
        self.tables = [
            [
                defaultdict(
                    RIPEntry,
                    {(j-1) : RIPEntry(j-1, 1)
                    for j in self.autoS["graph"][i]}),
                set(self.autoS["graph"][i])]
            for i in range(len(self.autoS["names"]))]
        self.used_m = True
        self.used = [False] * len(self.autoS["names"])


    def iteration(self):
        new_tables = deepcopy(self.tables)
        incremented = 0
        q = Queue()
        q.put(0)
        while not q.empty():
            u = q.get()
            self.used[u] = self.used_m
            new_tables[u][1] = set()
            upd = False
            for v in self.autoS["graph"][u]:
                rows, updated = self.tables[v-1]
                # v, e выплюснутые
                for e in (updated - {u + 1}):
                    if rows[e-1].metric + 1 < self.tables[u][0][e-1].metric:
                        upd = True
                        new_tables[u][1].add(e)
                        new_tables[u][0][e-1] = RIPEntry(v-1, rows[e-1].metric + 1)
                
                if self.used[v-1] != self.used_m:
                    q.put(v-1)
            incremented += upd
                
        self.used_m = not self.used_m
        self.tables = deepcopy(new_tables)
        
        return incremented

    
    def __repr__(self):
        res = ""
        for num, name in enumerate(self.autoS["names"]):
            res = res + "-" * 88 + "\r\n"
            res = res + "{:^88}\r\n".format("Router " + name)
            res = res + "-" * 88 + "\r\n"
            res = res + \
                self.PRINT_FMT.format(
                    "[Source IP]",
                    "[Destination IP]",
                    "[Next Hop]",
                    "[Metric]")
            for dst in self.tables[num][0]:
                res = res + \
                    self.PRINT_FMT.format(
                        name,
                        self.autoS["names"][dst],
                        self.autoS["names"][self.tables[num][0][dst].next_hop],
                        self.tables[num][0][dst].metric)
            res = res + "\r\n"
        return res

if __name__ == "__main__":
    quiet = "quiet" in os.environ and os.environ["quiet"] == "true"
    emulator = RIP("AS.json")
    if not quiet:
        print("{:^88}".format("STEP 0 [INITIAL]"))
        print("-" * 88)
        print(emulator)
    step = 1
    upd = emulator.iteration()
    while upd > 0:
        if not quiet:
            print("{:^88}".format(f"STEP {step} [UPDATED: {upd}]"))
            print("-" * 88)
            print(emulator)
        upd = emulator.iteration()
        step += 1
    print("{:^88}".format("FINAL STATE"))
    print("-" * 88)
    print("-" * 88)
    print(emulator)

