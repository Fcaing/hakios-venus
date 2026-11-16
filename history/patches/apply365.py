P = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
src = open(P).read()

a = '\t\t\t\t\tprintf("pcie: 5:   21: apply-265 start chan 0/1/20/21: cmd wp 0x%08x befor ee 0x%08x mh 0x%08x\\n",'
assert src.count(a) == 1, ("anchor", src.count(a))
i = src.index(a)

block = """					if (pcie_erfull >= 2u) {	/* apply-365: wipe the er ring before the ee 2
								 * transition, so anything in it afterwards was
								 * written by the device and not by us. */
						uint32_t o5;

						for (o5 = 0; o5 < 0x1000; o5 += 4) {
							wr(pcie_dma_extra + 0x4000 + o5, 0u);
						}
						wr(pcie_dma_extra + 0x201c, (uint32_t)(PCIE_EXTRA_IOVA + 0x4000));
						wr(pcie_dma_extra + 0x2020, 0u);
						wr(pcie_dma_extra + 0x2024, (uint32_t)(PCIE_EXTRA_IOVA + 0x4000));
						wr(pcie_dma_extra + 0x2028, 0u);
						for (o5 = 0; o5 < 0x1000; o5 += 64) {
							__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + 0x4000 + o5) : "memory");
						}
						__asm__ volatile ("dsb sy" : : : "memory");
						printf("pcie: 5:   21: apply-365 er ring wiped, rp/wp back to 0x%08x\\n",
						    (uint32_t)(PCIE_EXTRA_IOVA + 0x4000));
					}
"""
src = src[:i] + block + src[i:]
open(P, "w").write(src)
print("apply-365 ok")
