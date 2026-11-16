#!/usr/bin/env python3
"""apply-416: acknowledge the events we read, the way a real host does.

Our er0 context has rp = 0xa0204060 (the device posted six events) but wp = 0xa0204000:
we have read them and never told the device.  Every real host advances ctxt wp to rp after
processing and rings the event doorbell (0x700 + er*8).  If the firmware's service layer is
waiting on that credit, this is cheap and testable.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-416: give the events back, then see whether the firmware wakes up. */
	if (pcie_mhi_data == 36u && smmu_state == 1 && pcie_dma_extra != 0 &&
	    rd(bar0.base + 0x128) == 2u) {
		uint32_t e416, rp416, wp416, i416;
		uint32_t base416 = rd(bar0.base + 0x20);	/* ERDBOFF */

		for (e416 = 0; e416 < 3u; e416++) {
			uint32_t coff = 0x2000u + e416 * 0x2cu;
			rp416 = rd(pcie_dma_extra + coff + 0x1cu);
			wp416 = rd(pcie_dma_extra + coff + 0x24u);
			printf("apply-416 a: er%u rbase 0x%08x len 0x%08x rp 0x%08x wp 0x%08x\n",
			    e416, rd(pcie_dma_extra + coff + 0x0cu), rd(pcie_dma_extra + coff + 0x14u),
			    rp416, wp416);
			if (rp416 != wp416) {
				wr(pcie_dma_extra + coff + 0x24u, rp416);
				__asm__ __volatile__("dsb sy" ::: "memory");
				wr(bar0.base + base416 + e416 * 8u + 4u, 0u);
				wr(bar0.base + base416 + e416 * 8u, rp416);
				printf("apply-416 b: er%u acknowledged, wp -> 0x%08x, rang 0x%08x\n",
				    e416, rp416, base416 + e416 * 8u);
			}
		}
		sleep_ms(20);
		for (e416 = 0; e416 < 3u; e416++) {
			uint32_t coff = 0x2000u + e416 * 0x2cu;
			printf("apply-416 c: er%u now rp 0x%08x wp 0x%08x\n", e416,
			    rd(pcie_dma_extra + coff + 0x1cu), rd(pcie_dma_extra + coff + 0x24u));
		}
		printf("apply-416 d: after ack ee 0x%08x mh 0x%08x ch20 0x%08x ch21 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48),
		    rd(pcie_dma_extra + 20u * 0x2cu), rd(pcie_dma_extra + 21u * 0x2cu));

		/* now ask for M2 again -- the state the real device sits in */
		wr(bar0.base + 0x38, (rd(bar0.base + 0x38) & ~0xff00u) | (4u << 8));
		for (i416 = 0; i416 < 60u; i416++) {
			sleep_ms(5);
			if ((rd(bar0.base + 0x48) & 0xff00u) != 0x0200u) {
				printf("apply-416 e: t=%u ms mh 0x%08x ee 0x%08x\n", i416 * 5u + 5u,
				    rd(bar0.base + 0x48), rd(bar0.base + 0x128));
				break;
			}
		}
		printf("apply-416 f: after m2 request mh 0x%08x ee 0x%08x ch20 st 0x%08x\n",
		    rd(bar0.base + 0x48), rd(bar0.base + 0x128), rd(pcie_dma_extra + 20u * 0x2cu));

		/* and the ring question: a bad payload pointer on ch20 */
		if (rd(bar0.base + 0x128) == 2u) {
			uint32_t off = 20u * 0x2cu;
			uint32_t cwp = rd(pcie_dma_extra + off + 0x24u);
			if (cwp >= PCIE_EXTRA_IOVA && cwp < PCIE_EXTRA_IOVA + PCIE_EXTRA_SIZE) {
				vm_offset_t t = pcie_dma_extra + (cwp - (uint32_t)PCIE_EXTRA_IOVA);
				wr(t + 0x00u, 0x80000000u);
				wr(t + 0x04u, 0u);
				wr(t + 0x08u, 0x00000010u);
				wr(t + 0x0cu, 0x00020200u);
				__asm__ __volatile__("dc civac, %0" :: "r"(t) : "memory");
				__asm__ __volatile__("dsb sy" ::: "memory");
				wr(pcie_dma_extra + off + 0x24u, cwp + 0x10u);
				wr(bar0.base + 0x300u + 20u * 8u + 4u, 0u);
				wr(bar0.base + 0x300u + 20u * 8u, cwp + 0x10u);
				printf("apply-416 g: bad tre queued, rung 0x3a0 <- 0x%08x\n", cwp + 0x10u);
			}
		}
		sleep_ms(300);
		printf("apply-416 h: end ee 0x%08x mh 0x%08x ch20 0x%08x er1 rp 0x%08x wp 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(pcie_dma_extra + 20u * 0x2cu),
		    rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x1cu), rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x24u));
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1
assert "apply-416" not in src

a = "pcie_mhi_data != 35u && pcie_chanstart != 0"
assert src.count(a) == 1
src = src.replace(a, "pcie_mhi_data != 35u && pcie_mhi_data != 36u && pcie_chanstart != 0")
b = "pcie_mhi_data != 35u) wr(pcie_dma_extra + 20 * 0x2c"
assert src.count(b) == 1
src = src.replace(b, "pcie_mhi_data != 35u && pcie_mhi_data != 36u) wr(pcie_dma_extra + 20 * 0x2c")

i = src.index(END)
src = src[:i] + BLOCK + src[i:]
assert src.count("apply-416 h:") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-416 ok")
