#!/usr/bin/env python3
"""Show the newest run's slice of a logdump, from its last XNULOADER banner on."""
import sys

P = sys.argv[1]
data = open(P, 'rb').read()
banner = b'== XNULOADER run (usb) =='
i = data.rfind(banner)
print('last banner at %d of %d' % (i, len(data)))
slice_ = data[i:] if i >= 0 else data
text = slice_.decode('latin1')
lines = text.split('\n')
print('slice has %d lines' % len(lines))
import re
want = re.compile(r'init|pcie|canary|redwood/sbin|directories|checks', re.I)
for n, line in enumerate(lines):
    line = line.rstrip('\r')
    if want.search(line):
        print('%5d %s' % (n, line[:160]))
