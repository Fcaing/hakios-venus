#!/bin/sh
# 从 /tmp/amss_hex.dis 提取指定 vaddr 范围的反汇编
# 用法: re-hx-dump.sh <lo-hex> <hi-hex>
LO=${1:-15ede00}
HI=${2:-15edee8}
python3 - "$LO" "$HI" <<'PY'
import sys, re
lo = int(sys.argv[1], 16); hi = int(sys.argv[2], 16)
pat = re.compile(r'^\s*([0-9a-f]+):')
for line in open('/tmp/amss_hex.dis'):
    m = pat.match(line)
    if not m:
        continue
    a = int(m.group(1), 16)
    if lo <= a < hi:
        print(line.rstrip())
PY
