import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

a = "\t\t\t\t\t\tfor (i2 = 0; i2 < 60; i2++) {\n\t\t\t\t\t\t\tsleep_ms(5);\n"
assert s.count(a) == 1
b = a + '''\t\t\t\t\t\t\tfor (k2 = 0; k2 < 0x100; k2 += 64) {
\t\t\t\t\t\t\t\t__asm__ volatile ("dc ivac, %0" : : "r" (pcie_dma_extra + 0x2000 + k2) : "memory");
\t\t\t\t\t\t\t}
\t\t\t\t\t\t\tfor (k2 = 0; k2 < 0x100; k2 += 64) {
\t\t\t\t\t\t\t\t__asm__ volatile ("dc ivac, %0" : : "r" (pcie_dma_extra + 0x4000 + k2) : "memory");
\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t__asm__ volatile ("dsb sy" : : : "memory");
'''
s = s.replace(a, b)

old_p = '''\t\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-282 t=%u ms ee 0x%08x mh 0x%08x er0 rp 0x%08x wp 0x%08x\\n",
\t\t\t\t\t\t\t\t    (unsigned)(i2 * 5), rd(bar0.base + 0x128), rd(bar0.base + 0x48),
\t\t\t\t\t\t\t\t    rd(pcie_dma_extra + 0x201c), rd(pcie_dma_extra + 0x2024));'''
assert s.count(old_p) == 1, s.count(old_p)
new_p = '''\t\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-284 t=%u ms ee 0x%08x mh 0x%08x er0 rp 0x%08x wp 0x%08x ch20 0x%08x ev0 %08x %08x\\n",
\t\t\t\t\t\t\t\t    (unsigned)(i2 * 5), rd(bar0.base + 0x128), rd(bar0.base + 0x48),
\t\t\t\t\t\t\t\t    rd(pcie_dma_extra + 0x201c), rd(pcie_dma_extra + 0x2024),
\t\t\t\t\t\t\t\t    rd(pcie_dma_extra + 20 * 0x2c),
\t\t\t\t\t\t\t\t    rd(pcie_dma_extra + 0x4000), rd(pcie_dma_extra + 0x4004));'''
s = s.replace(old_p, new_p)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-284: cache invalidate + channel state in the poll loop")