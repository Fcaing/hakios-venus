p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(p).read()
old = '''\t\t\t\tuint32_t g4 = rd(gcc.base + 0x6b004), g0 = rd(gcc.base + 0x6b000);
\t\t\t\tuint32_t g24 = rd(gcc.base + 0x6b024), g1c = rd(gcc.base + 0x6b01c);
\t\t\t\tuint32_t g14 = rd(gcc.base + 0x6b014);
\t\t\t\t/* star's gate, printed only: 0x6b004 bit31 is the pcie gdsc, 0x6b000 bit0 the block
\t\t\t\t * reset, and bit31 of each AXI cbcr is "clock off" */
\t\t\t\tprintf("pcie: 5:   21: gcc 6b004=0x%08x 6b000=0x%08x 6b024=0x%08x 6b01c=0x%08x 6b014=0x%08x\\n",
\t\t\t\t       g4, g0, g24, g1c, g14);
'''
if s.count(old) != 1:
    raise SystemExit("anchor not found exactly once: %d" % s.count(old))
s = s.replace(old, '''\t\t\t\t/* apply-149: the gcc reads moved to pcie_bar == 27, so that a hang here can
\t\t\t\t * only be the map or the write, not a register read */
''')
open(p, "w").write(s)
print("patched")
import subprocess
print(subprocess.run(["grep","-n","apply-149",p],capture_output=True,text=True).stdout)