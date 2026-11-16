import io
p="/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s=io.open(p,encoding="utf-8",errors="surrogateescape").read()
a='''						for (d9 = 0; d9 < 40; d9++) {'''
ins='''						/* apply-360: the decisive test.  Put ch20's chstate back to 1
						 * (enabled) ourselves.  If the device is really servicing the
						 * command ring it will rewrite 2 (running) within a few ms.  If it
						 * stays at 1 the device never touched this context and every "the
						 * command ring works" claim in this file has to be withdrawn. */
						{
							uint32_t oldst = rd(pcie_dma_extra + 20 * 0x2c);

							wr(pcie_dma_extra + 20 * 0x2c, (oldst & ~0xffu) | 1u);
							__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + 20 * 0x2c) : "memory");
							__asm__ volatile ("dsb sy" : : : "memory");
							printf("pcie: 5:   21: apply-360 ch20 state forced to 1: was 0x%08x now 0x%08x\\n",
							    oldst, rd(pcie_dma_extra + 20 * 0x2c));
							sleep_ms(200);
							__asm__ volatile ("dc ivac, %0" : : "r" (pcie_dma_extra + 20 * 0x2c) : "memory");
							printf("pcie: 5:   21: apply-360 ch20 state after 200 ms: 0x%08x (1 = device inert)\\n",
							    rd(pcie_dma_extra + 20 * 0x2c));
						}
'''
assert s.count(a)==1, s.count(a)
s=s.replace(a, ins+a)
io.open(p,"w",encoding="utf-8",errors="surrogateescape").write(s)
print("apply-360 ok")