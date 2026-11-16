#!/usr/bin/env python3
"""apply-386: is the channel data path off for every channel, or only for ch20?

p422/p423/p425 settled that ch20 never fetches and that nobody reads its doorbell.
What is still open is whether that is *channel specific* (the firmware never attached
this pipe) or *global* (the engine has its channel/DMA path disabled until something
enables it).  Venue: every channel the device itself marked RUNNING gets a bad TRE at
the head of its ring and a doorbell; a fetch shows up as SYS_ERR or an SMMU fault, a
channel that nobody looks at stays silent.

Order matters: ch20 and ch21 first (known inert), then the low hardware channels.  If
the engine faults on any of them the rest of the loop is skipped and the round reports
where it happened.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
MARK = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-386: ring every running channel's doorbell with a bad TRE and see who bites. */
	if (pcie_mhi_data == 9u && smmu_state == 1 && pcie_dma_extra != 0) {
		static const uint32_t chs86[6] = {20u, 21u, 0u, 1u, 4u, 5u};
		uint32_t i86, ch, cb, rbase86, off86, t86, ee86, mh86, gfsr86, fsr86, st86, hit86;
		printf("apply-386 start: ee 0x%08x mh 0x%08x\n", rd(bar0.base + 0x128), rd(bar0.base + 0x48));
		for (i86 = 0; i86 < 6u; i86++) {
			ch = chs86[i86];
			cb = pcie_dma_extra + ch * 0x2cu;
			st86 = rd(cb);
			rbase86 = rd(cb + 0x0cu);
			printf("apply-386 ch%u: st 0x%08x type 0x%08x eri 0x%08x rbase 0x%08x len 0x%08x rp 0x%08x wp 0x%08x\n",
			    ch, st86, rd(cb + 0x04u), rd(cb + 0x08u), rbase86, rd(cb + 0x14u),
			    rd(cb + 0x1cu), rd(cb + 0x24u));
			if ((st86 & 0xffu) != 2u || rbase86 < (uint32_t)PCIE_EXTRA_IOVA ||
			    rbase86 > (uint32_t)(PCIE_EXTRA_IOVA + 0x1c0000u)) {
				printf("apply-386 ch%u: not running or not in our window, skipped\n", ch);
				continue;
			}
			off86 = rbase86 - (uint32_t)PCIE_EXTRA_IOVA;
			wr(pcie_dma_extra + off86 + 0x00u, 0x00001000u);
			wr(pcie_dma_extra + off86 + 0x04u, 0x00000000u);
			wr(pcie_dma_extra + off86 + 0x08u, 0x00000040u);
			wr(pcie_dma_extra + off86 + 0x0cu, 0x00020200u);
			wr(cb + 0x24u, rbase86 + 0x10u);
			wr(cb + 0x28u, 0u);
			__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + off86) : "memory");
			__asm__ volatile ("dc civac, %0" : : "r" (cb) : "memory");
			__asm__ volatile ("dsb sy" : : : "memory");
			ee86 = rd(bar0.base + 0x128);
			mh86 = rd(bar0.base + 0x48);
			gfsr86 = rd(smmu_mmio + 0x48);
			fsr86 = rd(smmu_cb + 0x58);
			wr(bar0.base + 0x300 + ch * 8u + 4u, 0u);
			wr(bar0.base + 0x300 + ch * 8u, rbase86 + 0x10u);
			__asm__ volatile ("dsb sy" : : : "memory");
			hit86 = 0;
			for (t86 = 0; t86 < 200u; t86++) {
				sleep_ms(1);
				if (rd(bar0.base + 0x128) != ee86 || rd(bar0.base + 0x48) != mh86 ||
				    rd(smmu_mmio + 0x48) != gfsr86 || rd(smmu_cb + 0x58) != fsr86) {
					hit86 = 1;
					printf("apply-386 ch%u FETCHED at %u ms: ee 0x%08x mh 0x%08x gfsr 0x%08x fsr 0x%08x far 0x%08x:%08x\n",
					    ch, t86, rd(bar0.base + 0x128), rd(bar0.base + 0x48),
					    rd(smmu_mmio + 0x48), rd(smmu_cb + 0x58),
					    rd(smmu_cb + 0x64), rd(smmu_cb + 0x60));
					break;
				}
			}
			if (!hit86) {
				printf("apply-386 ch%u: silent after 200 ms (st 0x%08x wp 0x%08x)\n",
				    ch, rd(cb), rd(cb + 0x24u));
			} else {
				printf("apply-386 stop: channel %u is the one that reads its ring\n", ch);
				break;
			}
		}
		printf("apply-386 end: ee 0x%08x mh 0x%08x er0[2] %08x %08x %08x %08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(pcie_dma_extra + 0x4020u),
		    rd(pcie_dma_extra + 0x4024u), rd(pcie_dma_extra + 0x4028u), rd(pcie_dma_extra + 0x402cu));
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()

old = "pcie_mhi_data != 4u && pcie_mhi_data != 5u && pcie_mhi_data != 6u && pcie_mhi_data != 7u && pcie_mhi_data != 8u"
new = old + " && pcie_mhi_data != 9u"
assert src.count(old) == 2, "expected the two ordering gates, found %d" % src.count(old)
src = src.replace(old, new)

assert src.count(MARK) == 1, "the apply-169 marker is not unique"
assert "apply-386" not in src, "apply-386 is already in the source"
src = src.replace(MARK, BLOCK + MARK)

io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-386 ok")
