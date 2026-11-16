import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
anchor = "\t\t\t\t\tif (smmu_state == 1 && pcie_dma_extra != 0 && pcie_mhi_late0 != 0) {\n\t\t\t\t\t\tuint32_t m0old = rd(bar0.base + 0x38);"
assert s.count(anchor) == 1, s.count(anchor)
block = '''\t\t\t\t\tif (smmu_state == 1 && pcie_dma_extra != 0 && pcie_mhi_late0 != 0 &&
\t\t\t\t\t    rd(bar0.base + 0x128) == 2u) {
\t\t\t\t\t\tunsigned k3;

\t\t\t\t\t\tprintf("pcie: 5:   21: apply-288 m0 at mission: before mh 0x%08x ee 0x%08x er0 wp 0x%08x\\n",
\t\t\t\t\t\t    rd(bar0.base + 0x48), rd(bar0.base + 0x128),
\t\t\t\t\t\t    *(volatile uint32_t *)(pcie_dma_extra + 0x2024));
\t\t\t\t\t\twr(bar0.base + 0x38, 2u << 8);
\t\t\t\t\t\tsleep_ms(5);
\t\t\t\t\t\tprintf("pcie: 5:   21: apply-288 after m0: mh 0x%08x ee 0x%08x ctrl 0x%08x\\n",
\t\t\t\t\t\t    rd(bar0.base + 0x48), rd(bar0.base + 0x128), rd(bar0.base + 0x38));
\t\t\t\t\t\tfor (k3 = 0; k3 < 30; k3++) {
\t\t\t\t\t\t\tuint32_t ev0;

\t\t\t\t\t\t\tsleep_ms(20);
\t\t\t\t\t\t\t__asm__ volatile ("dc ivac, %0" : : "r" (pcie_dma_extra + 0x4000) : "memory");
\t\t\t\t\t\t\t__asm__ volatile ("dsb sy" : : : "memory");
\t\t\t\t\t\t\tev0 = *(volatile uint32_t *)(pcie_dma_extra + 0x4000);
\t\t\t\t\t\t\tif (k3 % 5 == 0 || ev0 != 0) {
\t\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-288 t=%u ms mh 0x%08x ee 0x%08x er0 wp 0x%08x ev0 %08x\\n",
\t\t\t\t\t\t\t\t    k3 * 20, rd(bar0.base + 0x48), rd(bar0.base + 0x128),
\t\t\t\t\t\t\t\t    *(volatile uint32_t *)(pcie_dma_extra + 0x2024), ev0);
\t\t\t\t\t\t\t}
\t\t\t\t\t\t}
\t\t\t\t\t}
'''
s = s.replace(anchor, block + anchor)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-288 inserted, new size", len(s))