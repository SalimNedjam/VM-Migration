#!/usr/bin/python
# @lint-avoid-python-3-compatibility-imports

from bcc import BPF
from socket import inet_ntop, AF_INET
from struct import pack
from time import sleep
from collections import namedtuple, defaultdict


TCPSessionKey = namedtuple('TCPSession', ['data_addr', 'laddr', 'lport', 'daddr', 'dport'])

def show_infos(bpf):
    while True:
        try:
            (_, _, _, _, _, msg_b) = bpf.trace_fields()
            msg = msg_b.decode('utf8')
            if "BPF_MIG:" in msg:
                print(msg)
        except ValueError:
            continue
        except KeyboardInterrupt:
            break




def get_ipv4_session_key(k):
    return TCPSessionKey(data_addr=k.data_addr,
                         laddr=inet_ntop(AF_INET, pack("I", k.saddr)),
                         lport=k.lport,
                         daddr=inet_ntop(AF_INET, pack("I", k.daddr)),
                         dport=k.dport)


def show_details(ipv4_recv_bytes):
    sum = 0
    exiting = False


    print('Output every %s secs. Hit Ctrl-C to end' % 1)
    print("%-30s %-21s %-21s %6s" % ("DATA_ADDR", "TO", "FROM", "SIZE"))
    while not exiting:
        try:
            sleep(1)
        except KeyboardInterrupt:
            exiting = True
            print("TOTAL: ", sum >> 10, "KB")

        # IPv4: build dict of all seen keys
        ipv4_throughput = defaultdict()
        for k, v in ipv4_recv_bytes.items():
            key = get_ipv4_session_key(k)
            ipv4_throughput[key] = v.value
        ipv4_recv_bytes.clear()



        # output
        for k, recv_bytes in sorted(ipv4_throughput.items()):
            sum = sum + int(recv_bytes)
            print("%-30d %-21s %-21s %6d" % ( 
                k.data_addr,
                k.laddr + ":" + str(k.lport),
                k.daddr + ":" + str(k.dport),
                int(recv_bytes)))


device = "lo"
#device = "wlp0s20f3"

b = BPF(src_file="xdp.c")
fn = b.load_func("migfilter", BPF.XDP)
b.attach_xdp(device, fn, 0)

ipv4_recv_bytes = b["ipv4_recv_bytes"]

show_details(ipv4_recv_bytes)

b.remove_xdp(device, 0)
