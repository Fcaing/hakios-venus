import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
anchor = """						printf("pcie: 5:   21: apply-292 send: tre ptr 0x%08x len 0x%08x dw1 0x%08x ch20 wp 0x%08x\\n","""
assert s.count(anchor) == 1
block = """						/* apply-319: dump the whole channel context area so the real
						 * stride can be read off the image instead of assumed. */
						{
							uint32_t dq;

							for (dq = 0x0300; dq < 0x0400; dq += 64) {
								__asm__ volatile ("dc ivac, %0" : : "r" (pcie_dma_extra + dq) : "memory");
							}
							__asm__ volatile ("dsb sy" : : : "memory");
							for (dq = 0x0300; dq < 0x0400; dq += 0x10) {
								printf("pcie: 5:   21: apply-319 ctxt[%03x] %08x %08x %08x %08x\\n", dq,
								    rd(pcie_dma_extra + dq), rd(pcie_dma_extra + dq + 4),
								    rd(pcie_dma_extra + dq + 8), rd(pcie_dma_extra + dq + 12));
							}
						}
"""
s = s.replace(anchor, block + anchor)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-319 written")