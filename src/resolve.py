#!/usr/bin/env python3
import binascii
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

