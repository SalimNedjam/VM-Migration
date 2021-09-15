#!/usr/bin/env python

from bcc import BPF

BPF_PROGRAM=open(r"test.c", "r").read()




bpf = BPF(text = BPF_PROGRAM)
execve_function = bpf.get_syscall_fnname("clone")
bpf.attach_kretprobe(event = execve_function, fn_name = "hello") 
#bpf.trace_print()



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