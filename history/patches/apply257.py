import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
old = '''\t\t\t\t\tprintf("pcie: 5:   21: apply-252 t=0 ee 0x%08x mh 0x%08x ctrl 0x%08x err 0x%08x\\n",'''
assert s.count(old) == 1, s.count(old)
new = '''\t\t\t\t\twr(bar0.base + 0x700, rd(pcie_dma_extra + 0x2020));
\t\t\t\t\twr(bar0.base + 0x300 + 20 * 8, rd(pcie_dma_extra + 20 * 0x30 + 0x20));
\t\t\t\t\twr(bar0.base + 0x300 + 21 * 8, rd(pcie_dma_extra + 21 * 0x30 + 0x20));
\t\t\t\t\tprintf("pcie: 5:   21: apply-257 doorbells: er0 wp 0x%08x ch20 wp 0x%08x ch21 wp 0x%08x\\n",
\t\t\t\t\t    rd(pcie_dma_extra + 0x2028), rd(pcie_dma_extra + 20 * 0x30 + 0x28),
\t\t\t\t\t    rd(pcie_dma_extra + 21 * 0x30 + 0x28));
\t\t\t\t\tprintf("pcie: 5:   21: apply-252 t=0 ee 0x%08x mh 0x%08x ctrl 0x%08x err 0x%08x\\n",'''
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-257 done", len(s))