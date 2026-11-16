#!/usr/bin/env python3
"""apply-387: same question as apply-386, but without the static array.

p427 printed "apply-386 start" and then nothing at all - no channel line, no panic, no
second boot.  The only thing between that printf and the next one is the read of the
`static const uint32_t chs86[6]` array, so the prime suspect is constant data placed in
a section this build does not map (the fault would be swallowed by the loader's trap
handler and end the probe silently).  Here the channel numbers come from immediate
constants instead, and every step prints before it reads, so a silent stop points at
the exact instruction.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
START = "\t/* apply-386: ring every running channel's doorbell with a bad TRE and see who bites. */\n"
MARK = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-387: ring every running channel's doorbell with a bad TRE, no const data. */
	if (pcie_mhi_data == 10u && smmu_state == 1 && pcie_dma_extra != 0) {
		uint32_t i87, ch = 0, cb, rbase87, off87, t87, ee87, mh87, gfsr87, fsr87, st87, hit87;
		printf("apply-387 a: ee 0x%08x mh 0x%08x\n", rd(bar0.base + 0x128), rd(bar0.base + 0x48));
		for (i87 = 0; i87 < 6u; i87++) {
			if (i87 == 0u) {
				ch = 20u;
			} else if (i87 == 1u) {
				ch = 21u;
			} else if (i87 == 2u) {
				ch = 0u;
			} else if (i87 == 3u) {
				ch = 1u;
			} else if (i87 == 4u) {
				ch = 4u;
			} else {
				ch = 5u;
			}
			cb = pcie_dma_extra + ch * 0x2cu;
			printf("apply-387 b: channel %u at +0x%08x\n", ch, ch * 0x2cu);
			st87 = rd(cb);
			rbase87 = rd(cb + 0x0cu);
			printf("apply-387 c ch%u: st 0x%08x type 0x%08x eri 0x%08x rbase 0x%08x len 0x%08x rp 0x%08x wp 0x%08x\n",
			    ch, st87, rd(cb + 0x04u), rd(cb + 0x08u), rbase87, rd(cb + 0x14u),
			    rd(cb + 0x1cu), rd(cb + 0x24u));
			if ((st87 & 0xffu) != 2u || rbase87 < (uint32_t)PCIE_EXTRA_IOVA ||
			    rbase87 > (uint32_t)(PCIE_EXTRA_IOVA + 0x1c0000u)) {
				printf("apply-387 d ch%u: skipped (not running or outside our window)\n", ch);
				continue;
			}
			off87 = rbase87 - (uint32_t)PCIE_EXTRA_IOVA;
			wr(pcie_dma_extra + off87 + 0x00u, 0x00001000u);
			wr(pcie_dma_extra + off87 + 0x04u, 0x00000000u);
			wr(pcie_dma_extra + off87 + 0x08u, 0x00000040u);
			wr(pcie_dma_extra + off87 + 0x0cu, 0x00020200u);
			wr(cb + 0x24u, rbase87 + 0x10u);
			wr(cb + 0x28u, 0u);
			__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + off87) : "memory");
			__asm__ volatile ("dc civac, %0" : : "r" (cb) : "memory");
			__asm__ volatile ("dsb sy" : : : "memory");
			printf("apply-387 e ch%u: tre queued at 0x%08x, ringing 0x%08x\n",
			    ch, (uint32_t)(PCIE_EXTRA_IOVA + off87), 0x300u + ch * 8u);
			ee87 = rd(bar0.base + 0x128);
			mh87 = rd(bar0.base + 0x48);
			gfsr87 = rd(smmu_mmio + 0x48);
			fsr87 = rd(smmu_cb + 0x58);
			wr(bar0.base + 0x300 + ch * 8u + 4u, 0u);
			wr(bar0.base + 0x300 + ch * 8u, rbase87 + 0x10u);
			__asm__ volatile ("dsb sy" : : : "memory");
			hit87 = 0;
			for (t87 = 0; t87 < 200u; t87++) {
				sleep_ms(1);
				if (rd(bar0.base + 0x128) != ee87 || rd(bar0.base + 0x48) != mh87 ||
				    rd(smmu_mmio + 0x48) != gfsr87 || rd(smmu_cb + 0x58) != fsr87) {
					hit87 = 1;
					printf("apply-387 f ch%u FETCHED at %u ms: ee 0x%08x mh 0x%08x gfsr 0x%08x fsr 0x%08x far 0x%08x:%08x\n",
					    ch, t87, rd(bar0.base + 0x128), rd(bar0.base + 0x48),
					    rd(smmu_mmio + 0x48), rd(smmu_cb + 0x58),
					    rd(smmu_cb + 0x64), rd(smmu_cb + 0x60));
					break;
				}
			}
			if (hit87) {
				printf("apply-387 g: channel %u is the one that reads its ring, stopping\n", ch);
				break;
			}
			printf("apply-387 g ch%u: silent after 200 ms (st 0x%08x wp 0x%08x)\n",
			    ch, rd(cb), rd(cb + 0x24u));
		}
		printf("apply-387 h end: ee 0x%08x mh 0x%08x er0[2] %08x %08x %08x %08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(pcie_dma_extra + 0x4020u),
		    rd(pcie_dma_extra + 0x4024u), rd(pcie_dma_extra + 0x4028u), rd(pcie_dma_extra + 0x402cu));
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()

assert src.count(START) == 1, "apply-386 block marker not found"
a = src.index(START)
b = src.index(MARK, a)
src = src[:a] + BLOCK + src[b:]

old = "pcie_mhi_data != 9u"
new = "pcie_mhi_data != 9u && pcie_mhi_data != 10u"
assert src.count(old) == 2, "expected the two ordering gates, found %d" % src.count(old)
src = src.replace(old, new)

assert "apply-387" not in src.replace(BLOCK, ""), "apply-387 is already in the source"
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-387 ok")
