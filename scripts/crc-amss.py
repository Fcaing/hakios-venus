#!/usr/bin/env python3
import zlib, io, sys

p = "/root/hakios/userland/root/fw/amss.bin"
d = io.open(p, "rb").read()
print("our amss: size %d crc32 0x%08x prefix(512K) 0x%08x" % (
    len(d), zlib.crc32(d) & 0xffffffff, zlib.crc32(d[:524288]) & 0xffffffff))
print("star table expects: size 5236304 crc32 0xb4376a2a prefix 0xb163aa48")
