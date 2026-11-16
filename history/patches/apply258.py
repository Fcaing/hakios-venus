import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
old = '''\t\t\t\t\tprintf("pcie: 5:   21: apply-252 done ee 0x%08x mh 0x%08x ctrl 0x%08x err 0x%08x\\n",'''
assert s.count(old) == 1, s.count(old)
new = '''\t\t\t\t\tprintf("pcie: 5:   21: apply-258 er0 rp 0x%08x wp 0x%08x ring %08x %08x %08x %08x; ch20 rp 0x%08x wp 0x%08x\\n",
\t\t\t\t\t    rd(pcie_dma_extra + 0x2020), rd(pcie_dma_extra + 0x2028),
\t\t\t\t\t    rd(pcie_dma_extra + 0x4000), rd(pcie_dma_extra + 0x4004),
\t\t\t\t\t    rd(pcie_dma_extra + 0x4008), rd(pcie_dma_extra + 0x400c),
\t\t\t\t\t    rd(pcie_dma_extra + 20 * 0x30 + 0x20), rd(pcie_dma_extra + 20 * 0x30 + 0x28));
\t\t\t\t\tprintf("pcie: 5:   21: apply-252 done ee 0x%08x mh 0x%08x ctrl 0x%08x err 0x%08x\\n",'''
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-258 done", len(s))