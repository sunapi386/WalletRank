#!/usr/bin/env python3
import binascii
import os
import subprocess
from typing import Optional
import bech32


def resolve_addr2stake(address: str) -> Optional[str]:
    hrp, by = bech32.bech32_decode(address)
    if hrp != 'addr':
        return None
    words = bech32.convertbits(by, 5, 8, False)
    res = ''
    for w in words:
        res = f'{res}{format(w, "x").zfill(2)}'
    mainnet_addr = f'e1{res[-56:]}'
    array = binascii.unhexlify(mainnet_addr)
    words = [x for x in array]
    bech32_words = bech32.convertbits(words, 8, 5)
    bech32_addr = bech32.bech32_encode('stake', bech32_words)
    return bech32_addr


def resolve_addr2stake_cli(address: str) -> str:
    """
     same as 'echo "e1$(echo {address} | ./bech32 | tail -c 57)" |./bech32 stake'
     It may be quicker to cache the address, result in a lookup table
    :param address: wallet address, such as
    addr1qxdvcswn0exwc2vjfr6u6f6qndfhmk94xjrt5tztpelyk4yg83zn9d4vrrtzs98lcl5u5q6mv7ngmg829xxvy3g5ydls7c76wu
    to
    019acc41d37e4cec299248f5cd27409b537dd8b53486ba2c4b0e7e4b54883c4532b6ac18d62814ffc7e9ca035b67a68da0ea298cc24514237f
    then last 56 bytes
    883c4532b6ac18d62814ffc7e9ca035b67a68da0ea298cc24514237f
    then convert to bech32
    stake1uxyrc3fjk6kp343gznlu06w2qddk0f5d5r4znrxzg52zxlclk0hlq

    :return: stake key, such as
    stake1uxyrc3fjk6kp343gznlu06w2qddk0f5d5r4znrxzg52zxlclk0hlq
    """
    absolute_path = os.path.dirname(__file__)
    relative_path = "cardano-wallet/bech32"
    full_path = os.path.join(absolute_path, relative_path)

    p1 = subprocess.Popen(["echo", address], stdout=subprocess.PIPE)
    p2 = subprocess.run([full_path], stdin=p1.stdout, capture_output=True)
    s = p2.stdout.strip().decode('utf-8')
    p3 = subprocess.Popen(["echo", f"e1{s[-56:]}"], stdout=subprocess.PIPE)
    p4 = subprocess.run([full_path, 'stake'], stdin=p3.stdout, capture_output=True)
    return p4.stdout.strip().decode('utf-8')

