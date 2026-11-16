#!/usr/bin/env python3
"""apply-424: hand the firmware a TRE without touching its channel context.

p468 showed the firmware builds the IPCR contexts itself (rbase 0xa020c000/0xa020d000, len
0x200, state 0x202) - everything we saw before was degraded by our own rewrite (brstmode 2->0,
chstate -> 1).  So the one combination never tested is: leave the context exactly as the
firmware left it, put a TRE at its write pointer, and hand it over with the doorbell alone.

Step 1 rings 0x3a0 with wp+16 and does not write ctx.wp.
Step 2 (only if step 1 is silent) also writes ctx.wp, the way the vendor driver does it.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-424: TRE with the firmware's own context untouched. */
	if (pcie_mhi_data == 44u && smmu_state == 1 && pcie_dma_extra != 0 &&
	    rd(bar0.base + 0x128) == 2u) {
		uint32_t wp424 = rd(pcie_dma_extra + 20u * 0x2cu + 0x24u);
		uint32_t rp424 = rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu);
		uint32_t rl424 = rd(pcie_dma_extra + 20u * 0x2cu + 0x14u);
		uint32_t rb424 = rd(pcie_dma_extra + 20u * 0x2cu + 0x0cu);
		uint32_t st424 = rd(pcie_dma_extra + 20u * 0x2cu);
		uint32_t k424, o424, pay424 = 0x00000000u, changed = 0u;
		vm_offset_t tre424, buf424;

		printf("apply-424 a: ch20 st 0x%08x rbase 0x%08x len 0x%08x rp 0x%08x wp 0x%08x\n",
		    st424, rb424, rl424, rp424, wp424);
		printf("apply-424 a: er1 rp 0x%08x wp 0x%08x er0 rp 0x%08x wp 0x%08x ee 0x%08x\n",
		    rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x1cu), rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x24u),
		    rd(pcie_dma_extra + 0x2000u + 0x1cu), rd(pcie_dma_extra + 0x2000u + 0x24u),
		    rd(bar0.base + 0x128));
		/* the payload the firmware would receive */
		buf424 = pcie_dma_extra + 0x3a0000u;
		for (k424 = 0; k424 < 8u; k424++)
			wr(buf424 + k424 * 4u, 0x5154524bu + k424);	/* "KRTQ" + n */
		__asm__ __volatile__("dc civac, %0" :: "r"(buf424) : "memory");
		if (wp424 >= (uint32_t)PCIE_EXTRA_IOVA && wp424 < (uint32_t)(PCIE_EXTRA_IOVA + 0x100000u)) {
			o424 = wp424 - (uint32_t)PCIE_EXTRA_IOVA;
			tre424 = pcie_dma_extra + o424;
			wr(tre424 + 0x00u, (uint32_t)(PCIE_EXTRA_IOVA + 0x3a0000u));
			wr(tre424 + 0x04u, 0u);
			wr(tre424 + 0x08u, 0x00000020u);
			wr(tre424 + 0x0cu, 0x00020200u);
			__asm__ __volatile__("dc civac, %0" :: "r"(tre424) : "memory");
			__asm__ __volatile__("dsb sy" ::: "memory");
			/* doorbell only - no context write */
			wr(bar0.base + 0x300u + 20u * 8u + 4u, 0u);
			wr(bar0.base + 0x300u + 20u * 8u, wp424 + 0x10u);
			printf("apply-424 b: tre at 0x%llx, doorbell 0x%08x -> no ctx write\n",
			    (unsigned long long)tre424, wp424 + 0x10u);
		} else {
			printf("apply-424 b: wp 0x%08x outside the window\n", wp424);
		}
		for (k424 = 0; k424 < 200u; k424++) {
			sleep_ms(10);
			if (rd(pcie_dma_extra + 20u * 0x2cu) != st424 ||
			    rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu) != rp424 ||
			    rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x24u) != rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x24u)) {
				changed = 1u;
				printf("apply-424 c: t=%u ms ch20 st 0x%08x rp 0x%08x wp 0x%08x ee 0x%08x\n",
				    k424 * 10u, rd(pcie_dma_extra + 20u * 0x2cu),
				    rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu), rd(pcie_dma_extra + 20u * 0x2cu + 0x24u),
				    rd(bar0.base + 0x128));
				break;
			}
		}
		printf("apply-424 d: doorbell-only %s after 2 s (ch20 st 0x%08x rp 0x%08x wp 0x%08x ee 0x%08x mh 0x%08x)\n",
		    changed ? "CHANGED" : "silent", rd(pcie_dma_extra + 20u * 0x2cu),
		    rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu), rd(pcie_dma_extra + 20u * 0x2cu + 0x24u),
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48));
		/* step 2: the vendor way - write ctx.wp as well */
		wr(pcie_dma_extra + 20u * 0x2cu + 0x24u, wp424 + 0x10u);
		wr(bar0.base + 0x300u + 20u * 8u + 4u, 0u);
		wr(bar0.base + 0x300u + 20u * 8u, wp424 + 0x10u);
		printf("apply-424 e: ctx wp written, rung again\n");
		for (k424 = 0; k424 < 100u; k424++) {
			sleep_ms(10);
			if (rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu) != rp424) {
				printf("apply-424 f: t=%u ms ch20 rp 0x%08x st 0x%08x\n", k424 * 10u,
				    rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu), rd(pcie_dma_extra + 20u * 0x2cu));
				break;
			}
		}
		printf("apply-424 g: end ch20 st 0x%08x rp 0x%08x wp 0x%08x ee 0x%08x\n",
		    rd(pcie_dma_extra + 20u * 0x2cu), rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu),
		    rd(pcie_dma_extra + 20u * 0x2cu + 0x24u), rd(bar0.base + 0x128));
		printf("apply-424 h: er1 %08x %08x %08x %08x | %08x %08x %08x %08x\n",
		    rd(pcie_dma_extra + 0x5000u + 0x00u), rd(pcie_dma_extra + 0x5000u + 0x04u),
		    rd(pcie_dma_extra + 0x5000u + 0x08u), rd(pcie_dma_extra + 0x5000u + 0x0cu),
		    rd(pcie_dma_extra + 0x5000u + 0x10u), rd(pcie_dma_extra + 0x5000u + 0x14u),
		    rd(pcie_dma_extra + 0x5000u + 0x18u), rd(pcie_dma_extra + 0x5000u + 0x1cu));
		printf("apply-424 i: payload %08x %08x %08x %08x\n",
		    rd(buf424 + 0x0u), rd(buf424 + 0x4u), rd(buf424 + 0x8u), rd(buf424 + 0xcu));
		printf("apply-424 done\n");
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1, "end marker"
assert "apply-424" not in src

a1 = "pcie_mhi_data != 42u && pcie_mhi_data != 43u && pcie_chanstart != 0"
a2 = "pcie_mhi_data != 42u && pcie_mhi_data != 43u) wr(pcie_dma_extra + 20 * 0x2c"
assert src.count(a1) == 1, "gate A"
assert src.count(a2) == 1, "gate B"
src = src.replace(a1, "pcie_mhi_data != 42u && pcie_mhi_data != 43u && pcie_mhi_data != 44u && pcie_chanstart != 0")
src = src.replace(a2, "pcie_mhi_data != 42u && pcie_mhi_data != 43u && pcie_mhi_data != 44u) wr(pcie_dma_extra + 20 * 0x2c")

a = src.index(END)
src = src[:a] + BLOCK + src[a:]
assert src.count("apply-424 done") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-424 ok")
