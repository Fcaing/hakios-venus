#!/usr/bin/env python3
"""apply-388: the apply-386/387 question, with the pointer bug fixed.

p427 and p428 both stopped dead on the first context read, right after printing the
channel offset - no panic, no second boot, just silence.  The cause is in my probe, not
in the device: `pcie_dma_extra` is a 64-bit pointer, and `uint32_t cb = pcie_dma_extra +
ch * 0x2cu` truncates it, so the read went to an unmapped 32-bit alias and the loader's
trap handler swallowed the fault.  Everything here keeps the offset in a uint32_t and
adds it to the pointer at the point of use, the way the rest of this file does it.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
START = "\t/* apply-387: ring every running channel's doorbell with a bad TRE, no const data. */\n"
MARK = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-388: ring every running channel's doorbell with a bad TRE (offsets only). */
	if (pcie_mhi_data == 11u && smmu_state == 1 && pcie_dma_extra != 0) {
		uint32_t i88, ch = 0, o88, rbase88, off88, t88, ee88, mh88, gfsr88, fsr88, st88, hit88;
		printf("apply-387 a: ee 0x%08x mh 0x%08x\n", rd(bar0.base + 0x128), rd(bar0.base + 0x48));
		for (i88 = 0; i88 < 6u; i88++) {
			if (i88 == 0u) {
				ch = 20u;
			} else if (i88 == 1u) {
				ch = 21u;
			} else if (i88 == 2u) {
				ch = 0u;
			} else if (i88 == 3u) {
				ch = 1u;
			} else if (i88 == 4u) {
				ch = 4u;
			} else {
				ch = 5u;
			}
			o88 = ch * 0x2cu;
			printf("apply-387 b: channel %u at +0x%08x\n", ch, o88);
			st88 = rd(pcie_dma_extra + o88);
			rbase88 = rd(pcie_dma_extra + o88 + 0x0cu);
			printf("apply-388 c ch%u: st 0x%08x type 0x%08x eri 0x%08x rbase 0x%08x len 0x%08x rp 0x%08x wp 0x%08x\n",
			    ch, st88, rd(pcie_dma_extra + o88 + 0x04u), rd(pcie_dma_extra + o88 + 0x08u),
			    rbase88, rd(pcie_dma_extra + o88 + 0x14u),
			    rd(pcie_dma_extra + o88 + 0x1cu), rd(pcie_dma_extra + o88 + 0x24u));
			if ((st88 & 0xffu) != 2u || rbase88 < (uint32_t)PCIE_EXTRA_IOVA ||
			    rbase88 > (uint32_t)(PCIE_EXTRA_IOVA + 0x1c0000u)) {
				printf("apply-388 d ch%u: skipped (not running or outside our window)\n", ch);
				continue;
			}
			off88 = rbase88 - (uint32_t)PCIE_EXTRA_IOVA;
			wr(pcie_dma_extra + off88 + 0x00u, 0x00001000u);
			wr(pcie_dma_extra + off88 + 0x04u, 0x00000000u);
			wr(pcie_dma_extra + off88 + 0x08u, 0x00000040u);
			wr(pcie_dma_extra + off88 + 0x0cu, 0x00020200u);
			wr(pcie_dma_extra + o88 + 0x24u, rbase88 + 0x10u);
			wr(pcie_dma_extra + o88 + 0x28u, 0u);
			__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + off88) : "memory");
			__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + o88) : "memory");
			__asm__ volatile ("dsb sy" : : : "memory");
			printf("apply-388 e ch%u: tre at 0x%08x, rp 0x%08x wp 0x%08x, ringing 0x%08x\n",
			    ch, (uint32_t)(PCIE_EXTRA_IOVA + off88), rd(pcie_dma_extra + o88 + 0x1cu),
			    rd(pcie_dma_extra + o88 + 0x24u), 0x300u + ch * 8u);
			ee88 = rd(bar0.base + 0x128);
			mh88 = rd(bar0.base + 0x48);
			gfsr88 = rd(smmu_mmio + 0x48);
			fsr88 = rd(smmu_cb + 0x58);
			wr(bar0.base + 0x300 + ch * 8u + 4u, 0u);
			wr(bar0.base + 0x300 + ch * 8u, rbase88 + 0x10u);
			__asm__ volatile ("dsb sy" : : : "memory");
			hit88 = 0;
			for (t88 = 0; t88 < 200u; t88++) {
				sleep_ms(1);
				if (rd(bar0.base + 0x128) != ee88 || rd(bar0.base + 0x48) != mh88 ||
				    rd(smmu_mmio + 0x48) != gfsr88 || rd(smmu_cb + 0x58) != fsr88) {
					hit88 = 1;
					printf("apply-388 f ch%u FETCHED at %u ms: ee 0x%08x mh 0x%08x gfsr 0x%08x fsr 0x%08x far 0x%08x:%08x\n",
					    ch, t88, rd(bar0.base + 0x128), rd(bar0.base + 0x48),
					    rd(smmu_mmio + 0x48), rd(smmu_cb + 0x58),
					    rd(smmu_cb + 0x64), rd(smmu_cb + 0x60));
					break;
				}
			}
			if (hit88) {
				printf("apply-388 g: channel %u is the one that reads its ring, stopping\n", ch);
				break;
			}
			printf("apply-388 g ch%u: silent after 200 ms (st 0x%08x wp 0x%08x)\n",
			    ch, rd(pcie_dma_extra + o88), rd(pcie_dma_extra + o88 + 0x24u));
		}
		printf("apply-388 h end: ee 0x%08x mh 0x%08x er0[2] %08x %08x %08x %08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(pcie_dma_extra + 0x4020u),
		    rd(pcie_dma_extra + 0x4024u), rd(pcie_dma_extra + 0x4028u), rd(pcie_dma_extra + 0x402cu));
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()

assert src.count(START) == 1, "apply-387 block marker not found"
a = src.index(START)
b = src.index(MARK, a)
src = src[:a] + BLOCK + src[b:]

old = "pcie_mhi_data != 10u"
new = "pcie_mhi_data != 10u && pcie_mhi_data != 11u"
assert src.count(old) == 2, "expected the two ordering gates, found %d" % src.count(old)
src = src.replace(old, new)

assert "apply-388" not in src.replace(BLOCK, ""), "apply-388 is already in the source"
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-388 ok")
