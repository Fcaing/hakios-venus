#!/usr/bin/env python3
"""apply-382: does the device fetch data TREs at all?

p422 left ch20 in the state the device itself made: chstate 2 (running), rbase
0xa020c000, rp 0xa020c000, wp 0xa020c020, two TREs queued, the channel doorbell
holding 0xa020c020 - and nothing happened.  But rp is host-owned for command
rings, so "rp did not move" proves nothing for channels either.  The vendor code
(mhi_init.c:1085) only sets chan_ctxt->rp once, at init, and never reads it back,
so the real evidence of consumption is a TX_EVENT.

This round puts a TX TRE whose payload pointer is a deliberately unmapped IOVA in
the first slot.  A device that fetches the ring has to fault reading the payload;
SYS_ERR or an SMMU fault is the proof.  Silence means the ring is never read.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
MARK = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-382: a bad TX payload pointer.  Fetching the ring means reading it. */
	if (pcie_mhi_data == 5u && smmu_state == 1 && pcie_dma_extra != 0) {
		uint32_t c82 = 20u * 0x2cu, t82, rp82, st0, e0, e1, chg = 0;
		uint32_t sg0 = 0, sg1 = 0, sf0 = 0, sf1 = 0;
		printf("apply-382 ctx20: st 0x%08x type 0x%08x eridx %u rbase 0x%08x len 0x%08x rp 0x%08x wp 0x%08x\n",
		    rd(pcie_dma_extra + c82), rd(pcie_dma_extra + c82 + 0x04u), rd(pcie_dma_extra + c82 + 0x08u),
		    rd(pcie_dma_extra + c82 + 0x0cu), rd(pcie_dma_extra + c82 + 0x14u),
		    rd(pcie_dma_extra + c82 + 0x1cu), rd(pcie_dma_extra + c82 + 0x24u));
		printf("apply-382 er ctx: er0 rp 0x%08x wp 0x%08x er1 rp 0x%08x wp 0x%08x mh 0x%08x ee 0x%08x\n",
		    rd(pcie_dma_extra + 0x201cu), rd(pcie_dma_extra + 0x2024u),
		    rd(pcie_dma_extra + 0x2048u), rd(pcie_dma_extra + 0x2050u),
		    rd(bar0.base + 0x48), rd(bar0.base + 0x128));
		for (t82 = 0; t82 < 8u; t82++) {
			printf("apply-382 before er0[%u] %08x %08x %08x %08x\n", t82,
			    rd(pcie_dma_extra + 0x4000u + t82 * 16u), rd(pcie_dma_extra + 0x4000u + t82 * 16u + 4u),
			    rd(pcie_dma_extra + 0x4000u + t82 * 16u + 8u), rd(pcie_dma_extra + 0x4000u + t82 * 16u + 12u));
		}
		rp82 = rd(pcie_dma_extra + c82 + 0x1cu);
		st0 = rd(pcie_dma_extra + 0x201cu);
		e0 = rd(pcie_dma_extra + 0x2048u);
		sg0 = rd(smmu_mmio + 0x48);
		sf0 = rd(smmu_cb + 0x58);
		wr(pcie_dma_extra + (rp82 - (uint32_t)PCIE_EXTRA_IOVA) + 0x00u, 0xa0100000u);
		wr(pcie_dma_extra + (rp82 - (uint32_t)PCIE_EXTRA_IOVA) + 0x04u, 0u);
		wr(pcie_dma_extra + (rp82 - (uint32_t)PCIE_EXTRA_IOVA) + 0x08u, 0x1000u);
		wr(pcie_dma_extra + (rp82 - (uint32_t)PCIE_EXTRA_IOVA) + 0x0cu, 0x00020200u);
		wr(pcie_dma_extra + c82 + 0x24u, rp82 + 16u);
		wr(pcie_dma_extra + c82 + 0x28u, 0u);
		__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + (rp82 - (uint32_t)PCIE_EXTRA_IOVA)) : "memory");
		__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + c82) : "memory");
		__asm__ volatile ("dsb sy" : : : "memory");
		printf("apply-382 queued bad tre at 0x%08x: %08x %08x %08x %08x wp 0x%08x\n", rp82,
		    rd(pcie_dma_extra + (rp82 - (uint32_t)PCIE_EXTRA_IOVA)),
		    rd(pcie_dma_extra + (rp82 - (uint32_t)PCIE_EXTRA_IOVA) + 4u),
		    rd(pcie_dma_extra + (rp82 - (uint32_t)PCIE_EXTRA_IOVA) + 8u),
		    rd(pcie_dma_extra + (rp82 - (uint32_t)PCIE_EXTRA_IOVA) + 12u), rp82 + 16u);
		wr(bar0.base + 0x300 + 20u * 8u + 4u, 0u);
		wr(bar0.base + 0x300 + 20u * 8u, rp82 + 16u);
		__asm__ volatile ("dsb sy" : : : "memory");
		for (t82 = 0; t82 < 500u; t82++) {
			sleep_ms(1);
			sg1 = rd(smmu_mmio + 0x48);
			sf1 = rd(smmu_cb + 0x58);
			e1 = rd(bar0.base + 0x128);
			if (sf1 != sf0 || sg1 != sg0 || e1 != 2u || rd(bar0.base + 0x48) != 0x201u ||
			    rd(pcie_dma_extra + 0x201cu) != st0 || rd(pcie_dma_extra + 0x2048u) != e0) {
				chg = 1;
				printf("apply-382 change at %u ms: gfsr 0x%08x fsr 0x%08x far 0x%08x:%08x ee 0x%08x mh 0x%08x er0 rp 0x%08x er1 rp 0x%08x st 0x%08x\n",
				    t82, sg1, sf1, rd(smmu_cb + 0x64), rd(smmu_cb + 0x60), e1, rd(bar0.base + 0x48),
				    rd(pcie_dma_extra + 0x201cu), rd(pcie_dma_extra + 0x2048u), rd(pcie_dma_extra + c82));
				break;
			}
		}
		printf("apply-382 end: changed %u after %u ms gfsr 0x%08x fsr 0x%08x ee 0x%08x mh 0x%08x\n",
		    chg, t82, rd(smmu_mmio + 0x48), rd(smmu_cb + 0x58), rd(bar0.base + 0x128), rd(bar0.base + 0x48));
		for (t82 = 0; t82 < 8u; t82++) {
			printf("apply-382 after er0[%u] %08x %08x %08x %08x\n", t82,
			    rd(pcie_dma_extra + 0x4000u + t82 * 16u), rd(pcie_dma_extra + 0x4000u + t82 * 16u + 4u),
			    rd(pcie_dma_extra + 0x4000u + t82 * 16u + 8u), rd(pcie_dma_extra + 0x4000u + t82 * 16u + 12u));
		}
		for (t82 = 0; t82 < 8u; t82++) {
			printf("apply-382 after er1[%u] %08x %08x %08x %08x\n", t82,
			    rd(pcie_dma_extra + 0x5000u + t82 * 16u), rd(pcie_dma_extra + 0x5000u + t82 * 16u + 4u),
			    rd(pcie_dma_extra + 0x5000u + t82 * 16u + 8u), rd(pcie_dma_extra + 0x5000u + t82 * 16u + 12u));
		}
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()

# data=5 must also leave the channel contexts alone
old = "pcie_mhi_data != 4u"
new = "pcie_mhi_data != 4u && pcie_mhi_data != 5u"
assert src.count(old) == 2, "expected the two data=4 gates, found %d" % src.count(old)
src = src.replace(old, new)

assert src.count(MARK) == 1, "the apply-169 marker is not unique"
assert "apply-382" not in src, "apply-382 is already in the source"
src = src.replace(MARK, BLOCK + MARK)

io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-382 ok")
