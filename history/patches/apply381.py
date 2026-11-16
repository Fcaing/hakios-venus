#!/usr/bin/env python3
"""apply-381: stop cancelling our own start command.

p420/p421 established two things: the device does read the command ring (four
CMD_COMPLETION events with code 1, and a forced SYS_ERR when the wp is moved
backwards), and we rewrite every channel context to ENABLED *after* the start
command has already been accepted.  So this round:

  * pcie_mhi_data=4 leaves the channel contexts exactly as the device left them
    (apply-308 skipped, apply-360's forced write skipped);
  * a final block reads ch20's real context, queues one TRE at the pointer the
    context holds, rings the channel doorbell, and watches rp for 400 ms.

Nothing else changes, so the only difference from p420 is the ordering.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
MARK = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-381: leave the channel contexts exactly as the device left them and
	 * just queue one TRE at the pointer the context already holds. */
	if (pcie_mhi_data == 4u && smmu_state == 1 && pcie_dma_extra != 0) {
		uint32_t c81 = 20u * 0x2cu, t81, rp81, wp81, st81, moved81 = 0;
		uint64_t b81 = PCIE_EXTRA_IOVA + 0xe000u;
		printf("apply-381 ctx: st 0x%08x rbase 0x%08x len 0x%08x rp 0x%08x wp 0x%08x ee 0x%08x mh 0x%08x\n",
		    rd(pcie_dma_extra + c81), rd(pcie_dma_extra + c81 + 0x0cu), rd(pcie_dma_extra + c81 + 0x14u),
		    rd(pcie_dma_extra + c81 + 0x1cu), rd(pcie_dma_extra + c81 + 0x24u),
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48));
		rp81 = rd(pcie_dma_extra + c81 + 0x1cu);
		wp81 = rd(pcie_dma_extra + c81 + 0x24u);
		if (wp81 == rp81) {
			/* ptr, dword[0] = length, dword[1] = type 2 (data) | flags */
			wr(pcie_dma_extra + (rp81 - (uint32_t)PCIE_EXTRA_IOVA) + 0x00u, (uint32_t)b81);
			wr(pcie_dma_extra + (rp81 - (uint32_t)PCIE_EXTRA_IOVA) + 0x04u, 0u);
			wr(pcie_dma_extra + (rp81 - (uint32_t)PCIE_EXTRA_IOVA) + 0x08u, 0x1000u);
			wr(pcie_dma_extra + (rp81 - (uint32_t)PCIE_EXTRA_IOVA) + 0x0cu, 0x00020200u);
			wp81 = rp81 + 16u;
			wr(pcie_dma_extra + c81 + 0x24u, wp81);
			wr(pcie_dma_extra + c81 + 0x28u, 0u);
			__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + (rp81 - (uint32_t)PCIE_EXTRA_IOVA)) : "memory");
			__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + c81) : "memory");
			__asm__ volatile ("dsb sy" : : : "memory");
			printf("apply-381 queued at 0x%08x: %08x %08x %08x %08x new wp 0x%08x\n",
			    rp81, rd(pcie_dma_extra + (rp81 - (uint32_t)PCIE_EXTRA_IOVA)),
			    rd(pcie_dma_extra + (rp81 - (uint32_t)PCIE_EXTRA_IOVA) + 4u),
			    rd(pcie_dma_extra + (rp81 - (uint32_t)PCIE_EXTRA_IOVA) + 8u),
			    rd(pcie_dma_extra + (rp81 - (uint32_t)PCIE_EXTRA_IOVA) + 12u), wp81);
		} else {
			printf("apply-381 ring not empty, ringing with the pointer it already has\n");
		}
		wr(bar0.base + 0x300 + 20u * 8u + 4u, 0u);
		wr(bar0.base + 0x300 + 20u * 8u, wp81);
		for (t81 = 0; t81 < 400u; t81++) {
			sleep_ms(1);
			st81 = rd(pcie_dma_extra + c81);
			if (rd(pcie_dma_extra + c81 + 0x1cu) != rp81 || (st81 & 0xffu) != 1u) {
				moved81 = 1;
				printf("apply-381 change at %u ms: st 0x%08x rp 0x%08x wp 0x%08x er0[0] %08x %08x %08x %08x\n",
				    t81, st81, rd(pcie_dma_extra + c81 + 0x1cu), rd(pcie_dma_extra + c81 + 0x24u),
				    rd(pcie_dma_extra + 0x4000u), rd(pcie_dma_extra + 0x4004u),
				    rd(pcie_dma_extra + 0x4008u), rd(pcie_dma_extra + 0x400cu));
				break;
			}
		}
		printf("apply-381 end: moved %u after %u ms st 0x%08x rp 0x%08x wp 0x%08x ee 0x%08x mh 0x%08x\n",
		    moved81, t81, rd(pcie_dma_extra + c81), rd(pcie_dma_extra + c81 + 0x1cu),
		    rd(pcie_dma_extra + c81 + 0x24u), rd(bar0.base + 0x128), rd(bar0.base + 0x48));
		for (t81 = 0; t81 < 8u; t81++) {
			printf("apply-381 er0[%u] %08x %08x %08x %08x\n", t81,
			    rd(pcie_dma_extra + 0x4000u + t81 * 16u), rd(pcie_dma_extra + 0x4000u + t81 * 16u + 4u),
			    rd(pcie_dma_extra + 0x4000u + t81 * 16u + 8u), rd(pcie_dma_extra + 0x4000u + t81 * 16u + 12u));
		}
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()

# 1) apply-308 must not run in data=4 mode: it wipes and rebuilds every channel
#    context after the start command was accepted.
old308 = "if (pcie_chanstart != 0 && smmu_state == 1 && pcie_dma_extra != 0 &&"
new308 = "if (pcie_mhi_data != 4u && pcie_chanstart != 0 && smmu_state == 1 && pcie_dma_extra != 0 &&"
assert src.count(old308) == 1, "apply-308 gate not found once: %d" % src.count(old308)
src = src.replace(old308, new308)

# 2) apply-360's forced write to ch20 chstate must not run either.
old360 = "wr(pcie_dma_extra + 20 * 0x2c, (oldst & ~0xffu) | 1u);"
new360 = "if (pcie_mhi_data != 4u) wr(pcie_dma_extra + 20 * 0x2c, (oldst & ~0xffu) | 1u);"
assert src.count(old360) == 1, "apply-360 write not found once: %d" % src.count(old360)
src = src.replace(old360, new360)

assert src.count(MARK) == 1, "the apply-169 marker is not unique"
assert "apply-381" not in src, "apply-381 is already in the source"
src = src.replace(MARK, BLOCK + MARK)

io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-381 ok")
