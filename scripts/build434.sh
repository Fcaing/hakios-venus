#!/bin/bash
set -o pipefail
cd /mnt/c/Users/Administrator/Documents/deepseek-harness/default-workspace/venus-recon
python3 apply434.py || exit 1
cd /root/hakios
bash tools/make-kernel.sh > /tmp/b434.log 2>&1
echo "exit=$?"
echo "errors=$(grep -c 'error:' /tmp/b434.log)"
ls -l hakios-kernel
echo "apply_tags=$(strings hakios-kernel | grep -c 'apply-')"
grep -n 'error:' /tmp/b434.log | head -6
exit 0