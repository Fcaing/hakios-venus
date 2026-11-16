#!/usr/bin/env python3
"""apply-427: brstmode.

ch0 (LOOPBACK) has chan_ctxt.word0 = 0x00000002 - RUNNING with brstmode 0 - and it *does*
consume TREs.  ch20 has 0x00000202 - RUNNING with brstmode 2 - and never consumes anything.
The vendor enum says 2 means "burst disabled", but this firmware's channel 20 was left at
0x202 by the firmware itself, so try the value the working channel uses.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-427: give ch20 the same brstmode the working LOOPBACK channel has. */
	if (pcie_mhi_data == 47u && smmu_state == 1 && pcie_dma_extra != 0 &&
	    rd(bar0.base + 0x128) == 2u) {
		uint32_t c427, wp427, rp427, st427, k427, w0427;
		vm_offset_t tre427, buf427;

		sleep_ms(1500);
		c427 = 20u * 0x2cu;
		w0427 = rd(pcie_dma_extra + c427);
		st427 = rd(pcie_dma_extra + 0u * 0x2cu);
		printf("apply-427 a: ch20 word0 0x%08x | ch0 word0 0x%08x | ch21 word0 0x%08x\n",
		    w0427, st427, rd(pcie_dma_extra + 21u * 0x2cu));

		buf427 = pcie_dma_extra + 0x3a0000u;
		for (k427 = 0; k427 < 8u; k427++)
			wr(buf427 + k427 * 4u, 0x5154524bu + k427);
		__asm__ __volatile__("dc civac, %0" :: "r"(buf427) : "memory");

		/* variant A: brstmode 0, state RUNNING - what ch0 looks like */
		wr(pcie_dma_extra + c427, (w0427 & ~0x300u) | 0x002u);
		rp427 = rd(pcie_dma_extra + c427 + 0x1cu);
		wp427 = rd(pcie_dma_extra + c427 + 0x24u);
		tre427 = pcie_dma_extra + (wp427 - (uint32_t)PCIE_EXTRA_IOVA);
		wr(tre427 + 0x00u, (uint32_t)(PCIE_EXTRA_IOVA + 0x3a0000u));
		wr(tre427 + 0x04u, 0u);
		wr(tre427 + 0x08u, 0x00000020u);
		wr(tre427 + 0x0cu, 0x00020200u);
		__asm__ __volatile__("dc civac, %0" :: "r"(tre427) : "memory");
		__asm__ __volatile__("dsb sy" ::: "memory");
		wr(pcie_dma_extra + c427 + 0x24u, wp427 + 0x10u);
		printf("apply-427 b: word0 -> 0x%08x, tre 0x%llx, wp -> 0x%08x\n",
		    rd(pcie_dma_extra + c427), (unsigned long long)tre427, wp427 + 0x10u);
		wr(bar0.base + 0x300u + 20u * 8u + 4u, 0u);
		wr(bar0.base + 0x300u + 20u * 8u, wp427 + 0x10u);
		for (k427 = 0; k427 < 300u; k427++) {
			sleep_ms(10);
			if (rd(pcie_dma_extra + c427 + 0x1cu) != rp427 ||
			    rd(pcie_dma_extra + c427) != ((w0427 & ~0x300u) | 0x002u))
				break;
		}
		printf("apply-427 c: after 3 s ch20 st 0x%08x rp 0x%08x wp 0x%08x ee 0x%08x mh 0x%08x er1 rp 0x%08x\n",
		    rd(pcie_dma_extra + c427), rd(pcie_dma_extra + c427 + 0x1cu), rd(pcie_dma_extra + c427 + 0x24u),
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48),
		    rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x1cu));

		/* variant B: brstmode 3 - the vendor's "enable" */
		wr(pcie_dma_extra + c427, (rd(pcie_dma_extra + c427) & ~0x300u) | 0x302u);
		wp427 = rd(pcie_dma_extra + c427 + 0x24u);
		tre427 = pcie_dma_extra + (wp427 - (uint32_t)PCIE_EXTRA_IOVA);
		wr(tre427 + 0x00u, (uint32_t)(PCIE_EXTRA_IOVA + 0x3a0000u));
		wr(tre427 + 0x04u, 0u);
		wr(tre427 + 0x08u, 0x00000020u);
		wr(tre427 + 0x0cu, 0x00020200u);
		__asm__ __volatile__("dc civac, %0" :: "r"(tre427) : "memory");
		__asm__ __volatile__("dsb sy" ::: "memory");
		wr(pcie_dma_extra + c427 + 0x24u, wp427 + 0x10u);
		wr(bar0.base + 0x300u + 20u * 8u + 4u, 0u);
		wr(bar0.base + 0x300u + 20u * 8u, wp427 + 0x10u);
		printf("apply-427 d: brst 3 rung <?->0x%08x st 0x%08x\n", wp427 + 0x10u, rd(pcie_dma_extra + c427));
		for (k427 = 0; k427 < 300u; k427++) {
			sleep_ms(10);
			if (rd(pcie_dma_extra + c427 + 0x1cu) != rp427)
				break;
		}
		printf("apply-427 e: end ch20 st 0x%08x rp 0x%08x wp 0x%08x ee 0x%08x er1 rp 0x%08x\n",
		    rd(pcie_dma_extra + c427), rd(pcie_dma_extra + c427 + 0x1cu), rd(pcie_dma_extra + c427 + 0x24u),
		    rd(bar0.base + 0x128), rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x1cu));
		printf("apply-427 f: payload %08x %08x %08x %08x\n",
		    rd(buf427 + 0x0u), rd(buf427 + 0x4u), rd(buf427 + 0x8u), rd(buf427 + 0xcu));
		printf("apply-427 done\n");
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1 and "apply-427" not in src

a1 = "pcie_mhi_data != 46u && pcie_chanstart != 0"
a2 = "pcie_mhi_data != 46u) wr(pcie_dma_extra + 20 * 0x2c"
assert src.count(a1) == 1, "gate A"
assert src.count(a2) == 1, "gate B"
src = src.replace(a1, "pcie_mhi_data != 46u && pcie_mhi_data != 47u && pcie_chanstart != 0")
src = src.replace(a2, "pcie_mhi_data != 46u && pcie_mhi_data != 47u) wr(pcie_dma_extra + 20 * 0x2c")

a = src.index(END)
src = src[:a] + BLOCK + src[a:]
assert src.count("apply-427 done") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-427 ok")
