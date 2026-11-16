import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
T = "\t" * 6
old = T + "unsigned d5;\n" + T + "volatile uint32_t *e5;\n\n" + T + '__asm__ volatile ("dc ivac, %0" : : "r" (pcie_dma_extra + 0x4000) : "memory");'
assert s.count(old) == 1, s.count(old)
new = (T + "unsigned d5, d6;\n" + T + "volatile uint32_t *e5;\n\n"
       + T + "for (d6 = 0; d6 < 0x1c00; d6 += 64) {\n"
       + T + "\t__asm__ volatile (\"dc ivac, %0\" : : \"r\" (pcie_dma_extra + d6) : \"memory\");\n"
       + T + "}\n"
       + T + '__asm__ volatile ("dc ivac, %0" : : "r" (pcie_dma_extra + 0x4000) : "memory");')
s = s.replace(old, new)
old2 = T + "for (d5 = 0; d5 < 4; d5++) {\n" + T + "\te5 = (volatile uint32_t *)(pcie_dma_extra + 0x4000 + d5 * 0x30);"
assert s.count(old2) == 1
s = s.replace(old2, T + "for (d5 = 0; d5 < 8; d5++) {\n" + T + "\te5 = (volatile uint32_t *)(pcie_dma_extra + 0x4000 + d5 * 0x10);")
s = s.replace("apply-291 ev[%02x] %08x %08x %08x %08x %08x %08x %08x %08x", "apply-293 ev[%02x] %08x %08x %08x %08x")
s = s.replace("d5 * 0x30, e5[0], e5[1], e5[2], e5[3], e5[4], e5[5], e5[6], e5[7]);", "d5 * 0x10, e5[0], e5[1], e5[2], e5[3]);")
s = s.replace("apply-291 final rp 0x%08x wp 0x%08x ch20 0x%08x ch21 0x%08x mh 0x%08x ee 0x%08x\\n", "apply-293 final rp 0x%08x wp 0x%08x ch20 0x%08x ch21 0x%08x mh 0x%08x ee 0x%08x ch20rp 0x%08x ch20wp 0x%08x\\n")
s = s.replace(T + "    rd(bar0.base + 0x48), rd(bar0.base + 0x128));", T + "    rd(bar0.base + 0x48), rd(bar0.base + 0x128),\n" + T + "    rd(pcie_dma_extra + 20 * 0x2c + 0x1c), rd(pcie_dma_extra + 20 * 0x2c + 0x24));")
io.open(p, "w", encoding="utf-8").write(s)
print("apply-293 in, size", len(s))