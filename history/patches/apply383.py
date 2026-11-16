#!/usr/bin/env python3
"""apply-383: where does the device think the channel contexts live?

Our channel contexts are at pcie_dma_extra + ch*0x2c, but the context-base
registers are programmed in one place (hakios.pcie.c:1764-1773) with
ECABAP = ctxt + 0x800 while the event contexts we read and mutate sit at
+0x2000.  If CCABAP points somewhere other than the channel array we write,
the device sees ch20 as disabled and will never fetch a TRE - which is exactly
what p422 and p423 showed.  Read-only round: dump the four bases and the two
candidate layouts.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
MARK = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-383: read the context bases and compare with where we put things. */
	if (pcie_mhi_data == 6u && smmu_state == 1 && pcie_dma_extra != 0) {
		uint32_t ccab = rd(bar0.base + 0x58), ecab = rd(bar0.base + 0x60), crcb = rd(bar0.base + 0x68);
		uint32_t lbase = rd(bar0.base + 0x80), llim = rd(bar0.base + 0x88);
		uint32_t i83;
		printf("apply-383 dev 0x%08x ccab 0x%08x ecab 0x%08x crcb 0x%08x lbase 0x%08x limit 0x%08x\n",
		    (uint32_t)PCIE_EXTRA_IOVA, ccab, ecab, crcb, lbase, llim);
		printf("apply-383 delta: ccab %d ecab %d crcb %d (offsets into our block)\n",
		    (int)(ccab - (uint32_t)PCIE_EXTRA_IOVA), (int)(ecab - (uint32_t)PCIE_EXTRA_IOVA),
		    (int)(crcb - (uint32_t)PCIE_EXTRA_IOVA));
		printf("apply-383 ch20 at 0x370: %08x %08x %08x %08x %08x %08x %08x %08x\n",
		    rd(pcie_dma_extra + 0x370u), rd(pcie_dma_extra + 0x374u), rd(pcie_dma_extra + 0x378u),
		    rd(pcie_dma_extra + 0x37cu), rd(pcie_dma_extra + 0x384u), rd(pcie_dma_extra + 0x38cu),
		    rd(pcie_dma_extra + 0x394u), rd(pcie_dma_extra + 0x398u));
		printf("apply-383 ch20 at 0x2370: %08x %08x %08x %08x %08x %08x %08x %08x\n",
		    rd(pcie_dma_extra + 0x2370u), rd(pcie_dma_extra + 0x2374u), rd(pcie_dma_extra + 0x2378u),
		    rd(pcie_dma_extra + 0x237cu), rd(pcie_dma_extra + 0x2384u), rd(pcie_dma_extra + 0x238cu),
		    rd(pcie_dma_extra + 0x2394u), rd(pcie_dma_extra + 0x2398u));
		printf("apply-383 er0 at 0x800: %08x %08x %08x %08x %08x %08x %08x %08x\n",
		    rd(pcie_dma_extra + 0x800u), rd(pcie_dma_extra + 0x804u), rd(pcie_dma_extra + 0x808u),
		    rd(pcie_dma_extra + 0x80cu), rd(pcie_dma_extra + 0x814u), rd(pcie_dma_extra + 0x81cu),
		    rd(pcie_dma_extra + 0x824u), rd(pcie_dma_extra + 0x82cu));
		printf("apply-383 er0 at 0x2000: %08x %08x %08x %08x %08x %08x %08x %08x\n",
		    rd(pcie_dma_extra + 0x2000u), rd(pcie_dma_extra + 0x2004u), rd(pcie_dma_extra + 0x2008u),
		    rd(pcie_dma_extra + 0x200cu), rd(pcie_dma_extra + 0x2014u), rd(pcie_dma_extra + 0x201cu),
		    rd(pcie_dma_extra + 0x2024u), rd(pcie_dma_extra + 0x202cu));
		printf("apply-383 cmd at 0x2400: %08x %08x %08x %08x %08x %08x\n",
		    rd(pcie_dma_extra + 0x2400u), rd(pcie_dma_extra + 0x2404u), rd(pcie_dma_extra + 0x2408u),
		    rd(pcie_dma_extra + 0x240cu), rd(pcie_dma_extra + 0x241cu), rd(pcie_dma_extra + 0x2424u));
		/* if ccab points inside our block, show the channel array exactly there */
		if (ccab >= (uint32_t)PCIE_EXTRA_IOVA && ccab < (uint32_t)PCIE_EXTRA_IOVA + 0x20000u) {
			uint32_t off83 = ccab - (uint32_t)PCIE_EXTRA_IOVA + 20u * 0x2cu;

			printf("apply-383 ch20 as the device sees it (block+0x%x): %08x %08x %08x %08x %08x %08x %08x %08x\n",
			    off83, rd(pcie_dma_extra + off83), rd(pcie_dma_extra + off83 + 4u),
			    rd(pcie_dma_extra + off83 + 8u), rd(pcie_dma_extra + off83 + 12u),
			    rd(pcie_dma_extra + off83 + 16u), rd(pcie_dma_extra + off83 + 24u),
			    rd(pcie_dma_extra + off83 + 28u), rd(pcie_dma_extra + off83 + 32u));
		}
		for (i83 = 0; i83 < 3u; i83++) {
			uint32_t rp83 = rd(pcie_dma_extra + 0x201cu + i83 * 0x2cu);

			printf("apply-383 er%u ctx rbase 0x%08x len 0x%08x rp 0x%08x wp 0x%08x\n", i83,
			    rd(pcie_dma_extra + 0x2000u + i83 * 0x2cu + 0x0cu),
			    rd(pcie_dma_extra + 0x2000u + i83 * 0x2cu + 0x14u), rp83,
			    rd(pcie_dma_extra + 0x2000u + i83 * 0x2cu + 0x24u));
		}
		printf("apply-383 mh 0x%08x ee 0x%08x cfg 0x%08x\n",
		    rd(bar0.base + 0x48), rd(bar0.base + 0x128), rd(bar0.base + 0x10));
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()

old = "pcie_mhi_data != 4u && pcie_mhi_data != 5u"
new = "pcie_mhi_data != 4u && pcie_mhi_data != 5u && pcie_mhi_data != 6u"
assert src.count(old) == 2, "expected the two ordering gates, found %d" % src.count(old)
src = src.replace(old, new)

assert src.count(MARK) == 1, "the apply-169 marker is not unique"
assert "apply-383" not in src, "apply-383 is already in the source"
src = src.replace(MARK, BLOCK + MARK)

io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-383 ok")
