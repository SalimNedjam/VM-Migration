
#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/in.h>
#include <linux/tcp.h>
#define ETH_HLEN 14



#define MAX_LEN 1500
#define MAX_LEN_LO 65536

struct ipv4_key_t {
    u32 saddr;
    u32 daddr;
    u16 lport;
    u16 dport;
    u64 data_addr;
};
BPF_HASH(ipv4_recv_bytes, struct ipv4_key_t);



int migfilter(struct xdp_md *ctx) {
    struct iphdr *ip;
    struct tcphdr *tcp;
    struct ethhdr *eth;
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    char *payload;
    unsigned int payload_size;
    
    //ETH
    eth = (struct ethhdr *)data;
    if (eth + 1 > (struct ethhdr *)data_end)
        return XDP_PASS;

    if (eth->h_proto != htons(ETH_P_IP)) {
        return XDP_PASS;
    }

    //IP
    ip = (struct iphdr *)(eth + 1);

    if (ip + 1 > (struct iphdr *)data_end)
        return XDP_PASS;

    if (ip->protocol != IPPROTO_TCP)
        return XDP_PASS;


    //TCP
    tcp = (struct tcphdr*)((u8 *)ip + ip->ihl * 4);
    if (tcp + 1 > (struct tcphdr *)data_end)
        return XDP_PASS;    

    if (tcp->dest != ntohs(4444))
        return XDP_PASS;
        

    //PAYLOAD
    if(htons(ip->tot_len) - (ip->ihl * 4) - (tcp->doff * 4) <= 0)
        return XDP_PASS;
    
    payload = (char *)tcp + (tcp->doff * 4);
	//payload_size = (htons(ip->tot_len) - (ip->ihl * 4) - (tcp->doff * 4));


    if((char *)data_end - 4 - payload <= 0)
        return XDP_PASS;

	payload_size = (char *)data_end - 4 - payload;

    if((void *)payload + payload_size > data_end)
        return XDP_PASS;


    struct ipv4_key_t ipv4_key = {};
    ipv4_key.saddr = ip->saddr;
    ipv4_key.daddr = ip->daddr;
    ipv4_key.lport = ntohs(tcp->source);
    ipv4_key.dport = ntohs(tcp->dest);
    ipv4_key.data_addr = (u64)payload;
    ipv4_recv_bytes.increment(ipv4_key, payload_size);

    for(unsigned int i = 0; i < MAX_LEN; i++) {
    
        uint8_t *byte1 = payload + i;
        uint8_t *byte2 = payload + i + 1;
        uint8_t *byte3 = payload + i + 2;

        if (byte1 + 3 > (uint8_t *)data_end)
            return XDP_PASS;

        if (*(byte1) == 'L' && *(byte2) == 'T' && *(byte3) == 'S') {
            *byte1 = 'X';
            *byte2 = 'X';
            *byte3 = 'X';
            
        }
                

        


    }
    return XDP_PASS;
}
