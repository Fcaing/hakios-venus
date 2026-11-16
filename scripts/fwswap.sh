#!/bin/bash
# fwswap.sh <absolute-path-to-amss.bin>  - install an amss image into the root volume and repack it.
set -e
SRC="$1"
[ -f "$SRC" ] || { echo "fwswap: no such file: $SRC"; exit 1; }
echo "fwswap: source $SRC"
md5sum "$SRC"
cd /root/hakios/userland
[ -f /root/amss-orig.bin ] || cp root/fw/amss.bin /root/amss-orig.bin
install -m 0644 "$SRC" root/fw/amss.bin
echo "fwswap: installed"
ls -l root/fw/amss.bin
md5sum root/fw/amss.bin
python3 ../tools/apfs/mkapfs.py -z --plain fw -o root.apfs redwood=root | tail -1
ls -l root.apfs
md5sum root.apfs
