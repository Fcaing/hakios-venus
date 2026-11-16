#!/bin/bash
# 预检 3：内核能否编译。判据：error: 计数为 0、hakios-kernel 产出、apply- 标记存在
set -u
cd /root/hakios || { echo "FATAL: /root/hakios missing"; exit 9; }

echo "=== tree ==="
ls -l /root/hakios/hakios-kernel 2>/dev/null || echo "(no kernel binary yet)"
echo "=== src mtime ==="
stat -c '%y %n' xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c

echo "=== build ==="
start=$(date +%s)
bash tools/make-kernel.sh > /tmp/mk-pre.log 2>&1
rc=$?
end=$(date +%s)
echo "exit=$rc elapsed=$((end-start))s"
echo "errors=$(grep -c 'error:' /tmp/mk-pre.log)"
echo "--- last 8 lines of log ---"
tail -8 /tmp/mk-pre.log

echo "=== binary ==="
ls -l hakios-kernel
echo "apply_tags=$(strings hakios-kernel | grep -c 'apply-')"
echo "=== last 3 apply tags in binary ==="
strings hakios-kernel | grep -o 'apply-[0-9]*' | sort -u | tail -3
