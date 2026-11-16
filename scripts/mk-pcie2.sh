# A payload for one PCIe experiment with as little log noise as possible.
#
#   mk-pcie2.sh p18 "pcie=1 pcie_step=2 pcie_power=1 pcie_after=1 pcie_no1=1"
#
# Same as mk-pcie.sh, but without gpu=1 and gl=1: the adreno driver prints
# thousands of lines while it brings the 3D core up, and the kernel's log ring
# keeps only its newest bytes -- those lines were pushing the PCIe probe's own
# output out of the logdump partition before the loader could flush it.
set -e
TAG=${1:?tag}
EXTRA=${2:-}
W=/mnt/c/Users/Administrator/Documents/deepseek-harness/default-workspace/venus-recon
cd /root/hakios || exit 1

CM="ufs=2 ufs_native=1 ufs_write=1 var_hfs=ufs_darwin_data adsp=1 pmic=1 bootcpu=7 cpus=8 cpufreq=1 touchscreen=1 buttons=1 sb_delay=45 loader_return_after=${RET:-200} $EXTRA pcie_tag=$TAG fbwidth=1440 fbheight=3200 debug=0x8"
python3 xnuloader/mkpayload.py -o out/p-$TAG.bin kernel=hakios-kernel \
    ramdisk=userland/root.apfs --cmdline "$CM" > /tmp/mkp-$TAG.log 2>&1 || { tail -5 /tmp/mkp-$TAG.log; exit 1; }

python3 - "$W" "$TAG" "$CM" <<'PY'
import os, sys, hashlib
W, tag, cm = sys.argv[1], sys.argv[2], sys.argv[3]
data = open('/root/hakios/out/p-%s.bin' % tag, 'rb').read()
open(os.path.join(W, 'p-%s.bin' % tag), 'wb').write(data)
print("p-%s.bin  %d bytes sha256 %s" % (tag, len(data), hashlib.sha256(data).hexdigest()))
print("cmdline: %s" % cm)
PY
