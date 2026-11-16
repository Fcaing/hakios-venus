import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
anchor = "\t\t\t\t\t}\n\t\t\t\t\tif (pcie_mhi_watch != 0 && smmu_state == 1 && pcie_dma_extra != 0) {"
print("anchor count", s.count(anchor))
assert s.count(anchor) == 1
block = '''\t\t\t\t\t}
\t\t\t\t\t{
\t\t\t\t\t\tunsigned d5;
\t\t\t\t\t\tvolatile uint32_t *e5;

\t\t\t\t\t\t__asm__ volatile ("dc ivac, %0" : : "r" (pcie_dma_extra + 0x4000) : "memory");
\t\t\t\t\t\t__asm__ volatile ("dc ivac, %0" : : "r" (pcie_dma_extra + 0x4040) : "memory");
\t\t\t\t\t\t__asm__ volatile ("dc ivac, %0" : : "r" (pcie_dma_extra + 0x4080) : "memory");
\t\t\t\t\t\t__asm__ volatile ("dsb sy" : : : "memory");
\t\t\t\t\t\tfor (d5 = 0; d5 < 4; d5++) {
\t\t\t\t\t\t\te5 = (volatile uint32_t *)(pcie_dma_extra + 0x4000 + d5 * 0x30);
\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-291 ev[%02x] %08x %08x %08x %08x %08x %08x %08x %08x\\n",
\t\t\t\t\t\t\t    d5 * 0x30, e5[0], e5[1], e5[2], e5[3], e5[4], e5[5], e5[6], e5[7]);
\t\t\t\t\t\t}
\t\t\t\t\t\tprintf("pcie: 5:   21: apply-291 final rp 0x%08x wp 0x%08x ch20 0x%08x ch21 0x%08x mh 0x%08x ee 0x%08x\\n",
\t\t\t\t\t\t    rd(pcie_dma_extra + 0x201c), rd(pcie_dma_extra + 0x2024),
\t\t\t\t\t\t    rd(pcie_dma_extra + 20 * 0x2c), rd(pcie_dma_extra + 21 * 0x2c),
\t\t\t\t\t\t    rd(bar0.base + 0x48), rd(bar0.base + 0x128));
\t\t\t\t\t}
\t\t\t\t\tif (pcie_mhi_watch != 0 && smmu_state == 1 && pcie_dma_extra != 0) {'''
s = s.replace(anchor, block)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-291 in, size", len(s))