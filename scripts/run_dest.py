#!/usr/bin/env python3
import json
import os
import queue
import select
import sys
import getopt
import socket
import subprocess
import tempfile
import threading
import time
from pathlib import Path
from threading import Thread
from typing import Optional, List, Dict
import re
from pexpect import pxssh


class PipeMonitor:

    def __init__(self, tmpdir: str):
        self._path = Path(tmpdir, "monitor.pipe")
        os.mkfifo(self._path)
        self._running = True

    def stop(self):
        self._running = False

    def write(self, data: str):
        with self._path.open("a") as in_:
            in_.write(data + "\n")
            in_.flush()

    def start_reader(self):
        def thread_reader():
            with self._path.open("r") as in_:
                while self._running:
                    r = in_.read()
                    print(r)

        t = Thread(target=thread_reader)
        t.start()
        t.join()


active = True
is_vanilla = False

class UnixSocketQMP:

    def __init__(self, tmpdir: str):
        self._path = Path(tmpdir, "qmp.socket")
        self._output = queue.Queue()
        self._sock = None
        self._running = True

    @property
    def path(self):
        return self._path

    def stop(self):
        self._running = False

    def init(self):

        # wait the vm creation of the qmp socket path
        while not self._path.exists():
            pass

        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sock.connect(str(self._path))

        def reader_cb(s):
            global active
            global f
            if is_vanilla:
                f = open("vanilla.out", "a")
            else:
                f = open("modified.out", "a")

            while self._running:
                try:
                    data = s.recv(1024)
                    data_str = data.decode('utf-8')
                    j = json.loads(data)
                    m = re.match(r".*(total time:.*ms).*(downtime:.*ms).*setup", data_str)
                    mdone = re.match(r'.*("event": "RESUME").*', data_str)
                    if m is not None:
                        print(m.group(1))
                        print(m.group(2))
                        f.write(m.group(1)+'\n')
                        f.write(m.group(2)+'\n')
                    elif mdone is not None:
                        print("Migration Done")
                        active = False
                    else:
                        pass
                    if "return" in j:
                        if len(j["return"]) != 0:
                            print(j["return"])
                    elif "event" in j:
                        print("Event: "+ j["event"])
                    else:
                        print(data_str)
                    self._output.put(j, block=False)
                except:
                    continue
            f.close()

        reader = Thread(target=reader_cb, args=(self._sock,))
        reader.start()
        reader.join()

    def send(self, data: Dict):
        self._sock.send(json.dumps(data).encode("utf-8"))

    def recv(self):
        data = self._sock.recv(1024)
        j = json.loads(data)
        return j


class VM:
    class VMThread(threading.Thread):

        def __init__(self, vm: "VM"):
            self._running = False
            self._vm = vm
            self._process = None
            self._initialized = False
            super().__init__()

        def stop(self):
            self._running = False

        def run(self):
            def thread_stream_reader(stream):
                while getattr(threading.currentThread(), "do_run", True):
                    output = stream.readline().decode("utf-8")
                    if output is not None and output != "":
                        print(output)
                    else:
                        break

            self._process = subprocess.Popen(self._vm.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self._running = True

            stderr_thread = Thread(target=thread_stream_reader, args=(self._process.stderr,))
            stderr_thread.start()

            stdout_thread = Thread(target=thread_stream_reader, args=(self._process.stdout,))
            stdout_thread.start()

            self._vm.qmp.init()

            self._initialized = True

            stderr_thread.join()
            stdout_thread.join()

    def __init__(self, name: str, mem_size: int, is_vanilla: bool, extra: Optional[List[str]] = None):
        tmpdir = tempfile.mkdtemp(suffix=name)

        # self.monitor = Monitor(tmpdir)
        self._qmp = UnixSocketQMP(tmpdir)

        self._cmd = []
        if is_vanilla:
            self._cmd += ["/home/dev/git/vm-migration-fingerprint/vanilla-qemu/install/bin/qemu-system-x86_64"]
            self._cmd += ["-L", "/home/dev/git/vm-migration-fingerprint/vanilla-qemu/pc-bios/"]

        else:
            self._cmd += ["/home/dev/git/vm-migration-fingerprint/qemu-5.2.0/install/bin/qemu-system-x86_64"]
            self._cmd += ["-L", "/home/dev/git/vm-migration-fingerprint/qemu-5.2.0/pc-bios/"]

        self._cmd += ["-boot", "d"]
        self._cmd += ["-enable-kvm"]
        self._cmd += ["-uuid", "71ca9116-a4a1-b799-dab5-01a483bce024"]
        self._cmd += ["-m", str(mem_size)]
        self._cmd += ["-qmp", f"unix:{self._qmp.path},server,nowait"]
        self._cmd += ["-drive", "file=/home/dev/git/vm-migration-fingerprint/scripts/foobar_dest.qcow2,if=virtio"]

        # self._cmd += ["-monitor", f"pipe:{self.monitor.path},nowait"]

        if extra is not None:
            self._cmd += extra

    @property
    def qmp(self):
        return self._qmp

    @property
    def cmd(self):
        return self._cmd

    def run(self):
        th = self.__class__.VMThread(self)
        th.start()
        return th

    def quit(self):
        th = self.__class__.VMThread(self)
        th.stop()
        try:
            self.qmp.send({"execute": "quit"})
        except:
            pass
        self.qmp.stop()

    def poweroff(self):
        th = self.__class__.VMThread(self)
        th.stop()
        try:
            self.qmp.send({"execute": "system_powerdown"})
        except:
            pass
        self.qmp.stop()
def show_param():
    print('MIGRATION PARAMS:')
    print(' -v for vanilla, -f for fingerprint mode (DEFAULT: fingerprint mode)')
    print(' -b for disk migration WAN (DEFAULT: OFF)')
    print(' --vm-memory SIZE for RAM size of the VM (DEFAULT: 5120MB)')
    print(' --src-out PATH for the path of result json file source side (DEFAULT: ./src_out.json)')
    print(' --dst-out PATH for the path of result json file destination side (DEFAULT: ./dst_out.json')
    print('BENCHMARK PARAMS:')
    print(' --stress-rate RATE for the percentage for dirty rate (DEFAULT: 0)')
    print(' --stress-pages PAGES for the number of page to dirty (DEFAULT: 2009600)')
    print(' -t TIME for benchmark timeout (DEFAULT: 3600)')

def main(argv):
    global vm_src
    global vm_dst
    global active
    global f
    global is_vanilla
    need_migrate_disk = False
    dst_out = os.path.dirname(os.path.abspath(__file__)) + "/dst_out.json"
    timeout = "3600"
    vm_memory = "5120"
    stress_pages = "2009600"
    stress_rate = "0"
    migration_target = "tcp:192.168.1.40:4444"
    try:
        opts, _ = getopt.getopt(argv, "t:vfhb", ['vm-memory=', 'stress-pages=', 'stress-rate=', 'src-out=', 'dst_out=',  ])
    except getopt.GetoptError:
        show_param()

        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            show_param()
            sys.exit()

        elif opt == '-v':
            is_vanilla = True

        elif opt == '-f':
            is_vanilla = False

        elif opt == '-b':
            need_migrate_disk = True

        elif opt == '-t':
            timeout = arg

        elif opt == '--vm-memory':
            vm_memory = arg
        
        elif opt == '--stress-pages':
            stress_pages = arg
        
        elif opt == '--stress-rate':
            stress_rate = arg
        
        elif opt == '--src-out':
            src_out = arg
        
        elif opt == '--dst-out':
            dst_out = arg

    vm_dst = VM("dest", vm_memory, is_vanilla, ["-incoming", f"{migration_target}"])
    j_dst = vm_dst.run()
    time.sleep(4)
 

    vm_dst.qmp.send({
        "execute": "qmp_capabilities"
    })

    cmd = ""

    while True:
        cmd = input()
        if cmd == "q":
            break
        vm_dst.qmp.send({"execute": "human-monitor-command", "arguments": {"command-line": cmd}})

    vm_dst.poweroff()
    j_dst.join()
    time.sleep(3)

if __name__ == "__main__":
    main(sys.argv[1:])
