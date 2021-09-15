/*
#include <uapi/linux/ptrace.h>
#include <net/sock.h>
#include <bcc/proto.h>

struct ipv4_key_t {
    u32 pid;
    u32 saddr;
    u32 daddr;
    u16 lport;
    u16 dport;
    u64 skaddr;
};
BPF_HASH(ipv4_recv_bytes, struct ipv4_key_t);




int kprobe__tcp_cleanup_rbuf(struct pt_regs *ctx, struct sock *sk, int copied)
{
    u32 pid = bpf_get_current_pid_tgid() >> 32;

    u16 dport = 0, family = sk->__sk_common.skc_family;
    u64 *val, zero = 0;

    if (copied <= 0)
        return 0;
    if (sk->__sk_common.skc_num == 4444) {
        struct ipv4_key_t ipv4_key = {.pid = pid};
        ipv4_key.saddr = sk->__sk_common.skc_rcv_saddr;
        ipv4_key.daddr = sk->__sk_common.skc_daddr;
        ipv4_key.lport = sk->__sk_common.skc_num;
        dport = sk->__sk_common.skc_dport;
        ipv4_key.skaddr = (u64)sk;
        ipv4_key.dport = ntohs(dport);
        ipv4_recv_bytes.increment(ipv4_key, copied);
        bpf_trace_printk("BPF_MIG: %d\n", copied);
    }

    return 0;
}
*/




#include <uapi/linux/ptrace.h>
#include <net/sock.h>
#include <bcc/proto.h>
#include <uapi/linux/bpf.h>
#include <uapi/linux/if_ether.h>
#include <uapi/linux/if_packet.h>
#include <uapi/linux/ip.h>
#include <uapi/linux/in.h>
#include <uapi/linux/tcp.h>
#include <uapi/linux/filter.h>
#include <uapi/linux/pkt_cls.h>
#include <bpf/bpf_helpers.h>

#define DATA_OFF (ETH_HLEN + offsetof(unsigned char, data))


struct ipv4_key_t {
    u32 pid;
    u32 saddr;
    u32 daddr;
    u16 lport;
    u16 dport;
    u64 skaddr;
};
BPF_HASH(ipv4_recv_bytes, struct ipv4_key_t);

int kprobe__tcp_rcv_established(struct pt_regs *ctx, struct sock *sk, struct sk_buff *skb)
{
    u32 pid = bpf_get_current_pid_tgid() >> 32;
    u8 c = '0';
    u16 dport = 0, family = sk->__sk_common.skc_family;
    u64 *val, zero = 0;
    void *tmp;
    char *new_data;
    u32 size;
    bpf_probe_read(&size, sizeof(skb->data_len), ((char *)skb + offsetof(struct sk_buff, data_len)));

    if (sk->__sk_common.skc_num == 4444) {
        struct ipv4_key_t ipv4_key = {.pid = pid};
        ipv4_key.saddr = sk->__sk_common.skc_rcv_saddr;
        ipv4_key.daddr = sk->__sk_common.skc_daddr;
        ipv4_key.lport = sk->__sk_common.skc_num;
        dport = sk->__sk_common.skc_dport;
        ipv4_key.skaddr = (u64)skb;
        ipv4_key.dport = ntohs(dport);

        ipv4_recv_bytes.increment(ipv4_key, size);
        bpf_trace_printk("BPF_MIG: %p\n", size);

		//bpf_skb_store_bytes(skb, IP_SRC_OFF, &(ipv4_key.saddr), sizeof(ipv4_key.saddr), 0);
        //tmp = bpf_probe_read_kernel(skb->data, &c, 1);

        //memcpy(skb->data, &c, 1);
        }

    return 0;
}

//xdp