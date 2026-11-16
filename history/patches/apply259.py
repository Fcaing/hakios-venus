import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
old = '''\t\t\t\t\tprintf("pcie: 5:   21: apply-252 done ee 0x%08x mh 0x%08x ctrl 0x%08x err 0x%08x\\n",'''
assert s.count(old) == 1
new = '''\t\t\t\t\tprintf("pcie: 5:   21: apply-259 bhi st 0x%08x ec 0x%08x dbg %08x %08x %08x; mhi err 0x%08x %08x %08x %08x\\n",
\t\t\t\t\t    rd(bar0.base + 0x12c), rd(bar0.base + 0x130), rd(bar0.base + 0x134),
\t\t\t\t\t    rd(bar0.base + 0x138), rd(bar0.base + 0x13c),
\t\t\t\t\t    rd(bar0.base + 0x130), rd(bar0.base + 0x134),
\t\t\t\t\t    rd(bar0.base + 0x138), rd(bar0.base + 0x13c));
\t\t\t\t\tfor (w = 0; w < 3; w++) {
\t\t\t\t\t\tprintf("pcie: 5:   21: apply-259 er%u rbase 0x%08x rlen 0x%08x rp 0x%08x wp 0x%08x ring %08x %08x %08x %08x\\n",
\t\t\t\t\t\t    w, rd(pcie_dma_extra + 0x2000 + w * 0x30 + 0x10),
\t\t\t\t\t\t    rd(pcie_dma_extra + 0x2000 + w * 0x30 + 0x18),
\t\t\t\t\t\t    rd(pcie_dma_extra + 0x2000 + w * 0x30 + 0x20),
\t\t\t\t\t\t    rd(pcie_dma_extra + 0x2000 + w * 0x30 + 0x28),
\t\t\t\t\t\t    rd(pcie_dma_extra + 0x4000 + w * 0x1000),
\t\t\t\t\t\t    rd(pcie_dma_extra + 0x4000 + w * 0x1000 + 4),
\t\t\t\t\t\t    rd(pcie_dma_extra + 0x4000 + w * 0x1000 + 8),
\t\t\t\t\t\t    rd(pcie_dma_extra + 0x4000 + w * 0x1000 + 0xc));
\t\t\t\t\t}
\t\t\t\t\tprintf("pcie: 5:   21: apply-252 done ee 0x%08x mh 0x%08x ctrl 0x%08x err 0x%08x\\n",'''
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-259 done", len(s))