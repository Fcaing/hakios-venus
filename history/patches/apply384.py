#!/usr/bin/env python3
"""apply-384: does anything read channel 20's doorbell, and does the device answer a
START_CHAN for channel 20 at all?

p424 showed the device-visible context bases are right (CCABAP = CCRCBAP = our block,
channel array at +0, er at +0x2000, cmd at +0x2400) and ch20 reads running/tx/er1 with
a sane ring, so the "the device is looking at the wrong array" theory is dead.  Two
questions are left over from p422/p423:

  1. is DB 0x3a0 read by anyone?  Ring it with an IOVA that has no mapping at all; a
     device that fetches will fault, silence means the register is ignored.
  2. did the device ever process START_CHAN(20)?  p421 answered that with a SYS_ERR,
     but it had also moved the command wp backwards, which is what really upset the
     engine.  Here the wp only ever moves forward and we read the completion code.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
MARK = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-384: a bogus channel doorbell, then a forward-only START_CHAN(20). */
	if (pcie_mhi_data == 7u && smmu_state == 1 && pcie_dma_extra != 0) {
		uint32_t c84 = 20u * 0x2cu, t84, ee0, mh0, fs0, gf0, hit = 0;
		uint32_t cw84, off84, i84;
		printf("apply-384 start: ee 0x%08x mh 0x%08x ch20 %08x %08x rp 0x%08x wp 0x%08x cmd rp 0x%08x wp 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(pcie_dma_extra + c84),
		    rd(pcie_dma_extra + c84 + 0x04u), rd(pcie_dma_extra + c84 + 0x1cu),
		    rd(pcie_dma_extra + c84 + 0x24u), rd(pcie_dma_extra + 0x241cu), rd(pcie_dma_extra + 0x2424u));
		ee0 = rd(bar0.base + 0x128);
		mh0 = rd(bar0.base + 0x48);
		fs0 = rd(smmu_cb + 0x58);
		gf0 = rd(smmu_mmio + 0x48);
		wr(bar0.base + 0x300 + 20u * 8u + 4u, 0u);
		wr(bar0.base + 0x300 + 20u * 8u, 0x00001000u);
		__asm__ volatile ("dsb sy" : : : "memory");
		for (t84 = 0; t84 < 200u; t84++) {
			sleep_ms(1);
			if (rd(smmu_cb + 0x58) != fs0 || rd(smmu_mmio + 0x48) != gf0 ||
			    rd(bar0.base + 0x128) != ee0 || rd(bar0.base + 0x48) != mh0) {
				hit = 1;
				printf("apply-384 db 0x1000 reaction at %u ms: gfsr 0x%08x fsr 0x%08x far 0x%08x:%08x ee 0x%08x mh 0x%08x\n",
				    t84, rd(smmu_mmio + 0x48), rd(smmu_cb + 0x58), rd(smmu_cb + 0x64),
				    rd(smmu_cb + 0x60), rd(bar0.base + 0x128), rd(bar0.base + 0x48));
				break;
			}
		}
		printf("apply-384 db 0x1000: %s after %u ms\n", hit ? "someone fetched it" : "nobody read the doorbell", t84);
		if (!hit) {
			cw84 = rd(pcie_dma_extra + 0x2424u);
			off84 = 0x7000u + (cw84 - (uint32_t)(PCIE_EXTRA_IOVA + 0x7000u));
			wr(pcie_dma_extra + off84 + 0x00u, 0u);
			wr(pcie_dma_extra + off84 + 0x04u, 0u);
			wr(pcie_dma_extra + off84 + 0x08u, 0u);
			wr(pcie_dma_extra + off84 + 0x0cu, 0x14120000u);	/* start chan 20 */
			wr(pcie_dma_extra + 0x2424u, cw84 + 16u);
			wr(pcie_dma_extra + 0x2428u, 0u);
			__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + off84) : "memory");
			__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + 0x2400u) : "memory");
			__asm__ volatile ("dsb sy" : : : "memory");
			printf("apply-384 START_CHAN(20) at 0x%08x wp -> 0x%08x\n",
			    (uint32_t)(PCIE_EXTRA_IOVA + off84), cw84 + 16u);
			wr(bar0.base + 0x70, cw84 + 16u);
			for (t84 = 0; t84 < 300u; t84++) {
				sleep_ms(1);
			}
			for (i84 = 0; i84 < 12u; i84++) {
				printf("apply-384 er0[%u] %08x %08x %08x %08x\n", i84,
				    rd(pcie_dma_extra + 0x4000u + i84 * 16u), rd(pcie_dma_extra + 0x4000u + i84 * 16u + 4u),
				    rd(pcie_dma_extra + 0x4000u + i84 * 16u + 8u), rd(pcie_dma_extra + 0x4000u + i84 * 16u + 12u));
			}
			printf("apply-384 end: ee 0x%08x mh 0x%08x ch20 st 0x%08x rp 0x%08x wp 0x%08x\n",
			    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(pcie_dma_extra + c84),
			    rd(pcie_dma_extra + c84 + 0x1cu), rd(pcie_dma_extra + c84 + 0x24u));
		}
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()

old = "pcie_mhi_data != 4u && pcie_mhi_data != 5u && pcie_mhi_data != 6u"
new = "pcie_mhi_data != 4u && pcie_mhi_data != 5u && pcie_mhi_data != 6u && pcie_mhi_data != 7u"
assert src.count(old) == 2, "expected the two ordering gates, found %d" % src.count(old)
src = src.replace(old, new)

assert src.count(MARK) == 1, "the apply-169 marker is not unique"
assert "apply-384" not in src, "apply-384 is already in the source"
src = src.replace(MARK, BLOCK + MARK)

io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-384 ok")
