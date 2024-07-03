#!/usr/bin/env python3

from subprocess import check_output
import sys
import re

class Knight:
  def __init__(self, proc_name: str):
    self.proc_name = proc_name
    self.pid = int(check_output(["pgrep", "-f", self.proc_name]).splitlines()[0].decode('utf-8'))
    self.file = None
    self.remain = []

  def __enter__(self):
    self.file = open(f"/proc/{self.pid}/mem", 'rb+')
    return self

  def __exit__(self, exception_type, exception_value, exception_traceback):
    import os
    if (os.path.exists(f"/proc/{self.pid}/mem")):
      self.file.close()

  def search_for(self, val: int):
    if not self.remain:
      print("*** First search ***")
      mem_maps = check_output(["pmap", "-x", str(self.pid)]).decode('utf-8').splitlines()
      pattern = r'^([0-9a-f]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+rw.p*'
      for line in mem_maps:
        m = re.match(pattern, line)
        if not m:
          continue
        start = int(m.group(1), 16)
        size = int(m.group(2)) * 1024
        print(f"Scanning {hex(start)}--{hex(start+size)}")
        self.file.seek(start, 0)
        mem = self.file.read(size)
        for off in range(0, size, 4):
          if self.__bytes_to_int(mem[off: off+4]) == val:
            self.remain.append(start + off)
    else:
      print("*** Continue search ***")
      for addr in self.remain:
        self.file.seek(addr, 0)
        if self.__bytes_to_int(self.file.read(4)) != val:
          self.remain.remove(addr)
    print(f"There are {len(self.remain)} match(es).")

  def overwrite(self, val: int):
    nwrite = 0
    for addr in self.remain:
      self.file.seek(addr, 0)
      self.file.write(self.__int_to_bytes(val))
      nwrite += 1
    self.file.flush()
    print(f"{nwrite} value(s) written.")

  def reset(self):
    self.remain.clear()

  def __bytes_to_int(self, bytes):
    return int.from_bytes(bytes, byteorder=sys.byteorder)

  def __int_to_bytes(self, val, bytes=4):
    return int(val).to_bytes(bytes, byteorder=sys.byteorder)

def main():
  if len(sys.argv) != 2:
    print("Usage: python3 game.py <process_name>")
    return

  print(
    "Usage:\n"
        "  - s 100: search for value\n"
        "  - w 99999: overwrite value (for search matches)\n"
        "  - r: reset search\n")

  with Knight(sys.argv[1]) as k:
    while True:
      cmd = input(f"{k.proc_name} {k.pid}: ").strip()
      if cmd.startswith('q'):
        return
      elif cmd.startswith('s'):
        val = int(cmd.split()[1])
        k.search_for(val)
      elif cmd.startswith('w'):
        val = int(cmd.split()[1])
        k.overwrite(val)
      elif cmd.startswith('r'):
        k.reset()

if __name__ == "__main__":
  main()
