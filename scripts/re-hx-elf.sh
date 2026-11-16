#!/bin/sh
# 把 amss.bin 的 e_machine 改成 EM_HEXAGON(164) 后用 LLVM 反汇编，
# 搜索代码里对 32 位常量（如字符串地址 0x0160bbxx）的引用。
# 用法: re-hx-elf.sh <hex-imm-substring> [grep-context]
FW=/root/hakios/userland/root/fw/amss.bin
TARGET=${1:-160bb}
CTX=${2:-4}
python3 - <<'PY'
data = bytearray(open('/root/hakios/userland/root/fw/amss.bin','rb').read())
data[0x12:0x14] = (164).to_bytes(2, 'little')   # EM_HEXAGON
open('/tmp/amss_hex.elf','wb').write(bytes(data))
print("wrote /tmp/amss_hex.elf, e_machine=164, size=%d" % len(data))
PY
llvm-objdump -d --triple=hexagon --mcpu=hexagonv66 /tmp/amss_hex.elf > /tmp/amss_hex.dis 2>/tmp/amss_hex.err
echo "disasm lines: $(wc -l < /tmp/amss_hex.dis)  stderr: $(wc -l < /tmp/amss_hex.err)"
echo "=== hits for ##0x$TARGET ==="
grep -n -i -B"$CTX" -A"$CTX" "0x$TARGET" /tmp/amss_hex.dis | head -80
