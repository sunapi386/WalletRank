#!/usr/bin/env python3
import subprocess


def resolve_addr2stake(address: str) -> str:
    """
     same as 'echo "e1$(echo {address} | ./bech32 | tail -c 57)" |./bech32 stake'
     It may be quicker to cache the address, result in a lookup table
    :param address: wallet address, such as
    addr1q9f2prypgqkrmr5497d8ujl4s4qu9hx0w6kruspdkjyudc2xjgcagrdn0jxnf47yd96p7zdpfzny30l2jh5u5vwurxasjwukdr
    :return: stake key, such as
    stake1g6frr4qdkd7g6dxhc35hg8cf59y2vj9la227nj33msvmkczsmnx
    """
    p1 = subprocess.Popen(["echo", address], stdout=subprocess.PIPE)
    p2 = subprocess.run(['./cardano-wallet/bech32'], stdin=p1.stdout, capture_output=True)
    s = p2.stdout.strip().decode('utf-8')
    p3 = subprocess.Popen(["echo", s[-56:]], stdout=subprocess.PIPE)
    p4 = subprocess.run(['./cardano-wallet/bech32', 'stake'], stdin=p3.stdout, capture_output=True)
    return p4.stdout.strip().decode('utf-8')

# address = 'addr1q9f2prypgqkrmr5497d8ujl4s4qu9hx0w6kruspdkjyudc2xjgcagrdn0jxnf47yd96p7zdpfzny30l2jh5u5vwurxasjwukdr'
# resolve_addr2stake(address)
