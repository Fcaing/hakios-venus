import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

a1 = """						uint32_t d9;

						for (d9 = 0; d9 < 16; d9++) {"""
assert s.count(a1) == 1, s.count(a1)
s = s.replace(a1, """						uint32_t d9;
						uint32_t d9b;

						for (d9 = 0; d9 < 16; d9++) {""")

a2 = """							if (d9 % 10 == 0) {
								printf("pcie: 5:   21: apply-292 t=%u ms ch20 rp 0x%08x wp 0x%08x er0 rp 0x%08x mh 0x%08x ee 0x%08x\\n",
								    d9 * 10, rd(pcie_dma_extra + 20 * 0x2c + 0x1c), rd(pcie_dma_extra + 20 * 0x2c + 0x24),
								    rd(pcie_dma_extra + 0x201c), rd(bar0.base + 0x48), rd(bar0.base + 0x128));
							}"""
assert s.count(a2) == 1, s.count(a2)
s = s.replace(a2, """							if (d9 % 10 == 0) {
								/* apply-296: ch20 reports through er1, not er0.
								 * Read all three event contexts fresh, and read the
								 * channel doorbell back to see whether the write landed. */
								for (d9b = 0x2000; d9b < 0x2100; d9b += 64) {
									__asm__ volatile ("dc ivac, %0" : : "r" (pcie_dma_extra + d9b) : "memory");
								}
								__asm__ volatile ("dsb sy" : : : "memory");
								printf("pcie: 5:   21: apply-296 t=%u ms ch20 rp 0x%08x wp 0x%08x er0 %08x/%08x er1 %08x/%08x er2 %08x/%08x chdb 0x%08x mh 0x%08x ee 0x%08x\\n",
								    d9 * 10,
								    rd(pcie_dma_extra + 20 * 0x2c + 0x1c), rd(pcie_dma_extra + 20 * 0x2c + 0x24),
								    rd(pcie_dma_extra + 0x201c), rd(pcie_dma_extra + 0x2024),
								    rd(pcie_dma_extra + 1 * 0x2c + 0x1c), rd(pcie_dma_extra + 1 * 0x2c + 0x24),
								    rd(pcie_dma_extra + 2 * 0x2c + 0x1c), rd(pcie_dma_extra + 2 * 0x2c + 0x24),
								    rd(bar0.base + 0x300 + 20 * 8),
								    rd(bar0.base + 0x48), rd(bar0.base + 0x128));
							}""")
io.open(p, "w", encoding="utf-8").write(s)
print("patched", len(s))