import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
old = '''\t\t\t\t\t\tprintf("pcie: 5:   21: apply-288 m0 at mission: before mh 0x%08x ee 0x%08x er0 wp 0x%08x\\n",
\t\t\t\t\t\t    rd(bar0.base + 0x48), rd(bar0.base + 0x128),
\t\t\t\t\t\t    *(volatile uint32_t *)(pcie_dma_extra + 0x2024));
\t\t\t\t\t\twr(bar0.base + 0x38, 2u << 8);
\t\t\t\t\t\tsleep_ms(5);
\t\t\t\t\t\tprintf("pcie: 5:   21: apply-288 after m0: mh 0x%08x ee 0x%08x ctrl 0x%08x\\n",
\t\t\t\t\t\t    rd(bar0.base + 0x48), rd(bar0.base + 0x128), rd(bar0.base + 0x38));'''
assert s.count(old) == 1, s.count(old)
new = '''\t\t\t\t\t\tprintf("pcie: 5:   21: apply-289 ring er dbs at mission: before mh 0x%08x ee 0x%08x er0 wp 0x%08x\\n",
\t\t\t\t\t\t    rd(bar0.base + 0x48), rd(bar0.base + 0x128),
\t\t\t\t\t\t    *(volatile uint32_t *)(pcie_dma_extra + 0x2024));
\t\t\t\t\t\twr(bar0.base + 0x700, (uint32_t)(PCIE_EXTRA_IOVA + 0x4000 + 0xff0));
\t\t\t\t\t\twr(bar0.base + 0x708, (uint32_t)(PCIE_EXTRA_IOVA + 0x5000 + 0xff0));
\t\t\t\t\t\twr(bar0.base + 0x710, (uint32_t)(PCIE_EXTRA_IOVA + 0x6000 + 0xff0));
\t\t\t\t\t\tsleep_ms(5);
\t\t\t\t\t\tprintf("pcie: 5:   21: apply-289 after er dbs: mh 0x%08x ee 0x%08x ctrl 0x%08x\\n",
\t\t\t\t\t\t    rd(bar0.base + 0x48), rd(bar0.base + 0x128), rd(bar0.base + 0x38));'''
s = s.replace(old, new)
s = s.replace('apply-288 t=%u ms', 'apply-289 t=%u ms')
io.open(p, "w", encoding="utf-8").write(s)
print("apply-289 in, size", len(s))