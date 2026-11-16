#!/usr/bin/env python3
"""apply-394: 1 ms sampling of ch20/ch21 from the moment AMSS is up (data=17).

The question this round answers: does the firmware touch the IPCR channels at all in the first
few hundred milliseconds, even if it later gives up?  p418 caught EE going 2 -> 3 -> 2 within
0.46 s, which smells like an internal retry loop; if the channel contexts move during that
window we will see it here.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
START = "\t/* apply-393: "

BLOCK = r'''	/* apply-394: what the firmware does to the ipcr channels in its first 400 ms. */
	if (pcie_mhi_data == 17u && smmu_state == 1 && pcie_dma_extra != 0) {
		uint32_t i94, o94a = 20u * 0x2cu, o94b = 21u * 0x2cu;
		uint32_t s20 = 0xffffffffu, s21 = 0xffffffffu, e94 = 0xffffffffu;
		printf("apply-394 start: ee 0x%08x mh 0x%08x cfg 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(bar0.base + 0x10));
		printf("apply-394 t0 ch20 0x%08x rp 0x%08x wp 0x%08x | ch21 0x%08x rp 0x%08x wp 0x%08x | er0 %08x/%08x er1 %08x/%08x\n",
		    rd(pcie_dma_extra + o94a), rd(pcie_dma_extra + o94a + 0x1cu), rd(pcie_dma_extra + o94a + 0x24u),
		    rd(pcie_dma_extra + o94b), rd(pcie_dma_extra + o94b + 0x1cu), rd(pcie_dma_extra + o94b + 0x24u),
		    rd(pcie_dma_extra + 0x2000u + 0x1cu), rd(pcie_dma_extra + 0x2000u + 0x24u),
		    rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x1cu), rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x24u));
		for (i94 = 0; i94 < 400u; i94++) {
			uint32_t a = rd(pcie_dma_extra + o94a);
			uint32_t b = rd(pcie_dma_extra + o94b);
			uint32_t e = rd(bar0.base + 0x128);
			if (a != s20 || b != s21 || e != e94) {
				printf("apply-394 t=%u ms: ee 0x%08x mh 0x%08x ch20 0x%08x rp 0x%08x wp 0x%08x ch21 0x%08x rp 0x%08x wp 0x%08x er0 %08x/%08x er1 %08x/%08x\n",
				    i94, e, rd(bar0.base + 0x48),
				    a, rd(pcie_dma_extra + o94a + 0x1cu), rd(pcie_dma_extra + o94a + 0x24u),
				    b, rd(pcie_dma_extra + o94b + 0x1cu), rd(pcie_dma_extra + o94b + 0x24u),
				    rd(pcie_dma_extra + 0x2000u + 0x1cu), rd(pcie_dma_extra + 0x2000u + 0x24u),
				    rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x1cu), rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x24u));
				s20 = a; s21 = b; e94 = e;
			}
			sleep_ms(1);
		}
		printf("apply-394 end after 400 ms: ee 0x%08x mh 0x%08x ch20 0x%08x ch21 0x%08x er0 %08x/%08x er1 %08x/%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48),
		    rd(pcie_dma_extra + o94a), rd(pcie_dma_extra + o94b),
		    rd(pcie_dma_extra + 0x2000u + 0x1cu), rd(pcie_dma_extra + 0x2000u + 0x24u),
		    rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x1cu), rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x24u));
		for (i94 = 0; i94 < 6u; i94++)
			printf("apply-394 er0[%u] %08x %08x %08x %08x\n", i94,
			    rd(pcie_dma_extra + 0x4000u + i94 * 16u + 0x0u),
			    rd(pcie_dma_extra + 0x4000u + i94 * 16u + 0x4u),
			    rd(pcie_dma_extra + 0x4000u + i94 * 16u + 0x8u),
			    rd(pcie_dma_extra + 0x4000u + i94 * 16u + 0xcu));
		printf("apply-394 done\n");
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()

assert src.count(START) == 1, "apply-393 block marker not found"
a = src.index(START)
src = src[:a] + BLOCK + src[a:]

old = ("pcie_mhi_data != 12u && pcie_mhi_data != 13u && pcie_mhi_data != 14u && "
       "pcie_mhi_data != 15u && pcie_mhi_data != 16u")
assert src.count(old) == 2, "expected two gates, found %d" % src.count(old)
src = src.replace(old, old + " && pcie_mhi_data != 17u")

assert src.count("apply-394 done") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-394 ok")
