import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8", errors="surrogateescape").read()

anchor = "\t\t\t\t\t\twr(bar0.base + 0x70, (uint32_t)cwp2);\n\t\t\t\t\t\tfor (i2 = 0; i2 < 60; i2++) {\n\t\t\t\t\t\t\tsleep_ms(5);"
assert s.count(anchor) == 1, s.count(anchor)

add = anchor + """
							/* apply-321: the vendor queues its first data TRE 1.5 ms
							 * after the START_CHAN completion, so do the same here
							 * rather than waiting for the sampling loop to end. */
							if (i2 == 0 && pcie_mhi_data != 0) {
								volatile uint32_t *ft;
								ft = (volatile uint32_t *)(pcie_dma_extra + 0xc000);
								ft[0] = (uint32_t)(PCIE_EXTRA_IOVA + 0xe000);
								ft[1] = 0;
								ft[2] = 0x00000034;
								ft[3] = 0x00020200;
								for (k2 = 0; k2 < 0x100; k2 += 64) {
									__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + 0xc000 + k2) : "memory");
								}
								__asm__ volatile ("dsb sy" : : : "memory");
								*(volatile uint32_t *)(pcie_dma_extra + 20 * 0x2c + 0x1c) = (uint32_t)(PCIE_EXTRA_IOVA + 0xc000);
								*(volatile uint32_t *)(pcie_dma_extra + 20 * 0x2c + 0x20) = 0;
								*(volatile uint32_t *)(pcie_dma_extra + 20 * 0x2c + 0x24) = (uint32_t)(PCIE_EXTRA_IOVA + 0xc010);
								*(volatile uint32_t *)(pcie_dma_extra + 20 * 0x2c + 0x28) = 0;
								__asm__ volatile ("dsb sy" : : : "memory");
								wr(bar0.base + 0x300 + 20 * 8, (uint32_t)(PCIE_EXTRA_IOVA + 0xc010));
								printf("pcie: 5:   21: apply-321 fast data tre %08x %08x %08x %08x wp 0x%08x mh 0x%08x\\n",
								    ft[0], ft[1], ft[2], ft[3], (uint32_t)(PCIE_EXTRA_IOVA + 0xc010),
								    rd(bar0.base + 0x48));
							}"""
s = s.replace(anchor, add)
io.open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
print("apply-321 in, size", len(s))