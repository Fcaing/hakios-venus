#!/usr/bin/env python3
"""apply-408: when the firmware asserts, ask it why - dump the whole BHI block.

MRHI's BHI block (BAR0 + BHIOFF, which is 0x100 here) carries the download registers *and*
the firmware's own error report: STATUS, ERRCODE, ERRDBG1..3, SERIALNU, NUMSEG, MSMHWID.
The vendor's mhi_pm_sys_err_handler() reads exactly these after a SYS_ERR.  p452 already
showed errcode 0x0004161d (where earlier rounds read noise), so the values may be real.
This round asserts the firmware on purpose (START_CHAN(20), the reliable trigger) and then
reads the entire block, plus MHISTATUS and both event rings.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-408: assert ch20 on purpose, then dump the firmware's own error block. */
	if (pcie_mhi_data == 29u && smmu_state == 1 && pcie_dma_extra != 0 &&
	    rd(bar0.base + 0x128) == 2u) {
		uint32_t c408 = 20u * 0x2cu;
		uint32_t cwp408, off408, g408, ee408;
		uint32_t bo408 = rd(bar0.base + 0x28);	/* BHIOFF */

		printf("apply-408 a: bhioff 0x%08x bhiest 0x%08x ee 0x%08x mh 0x%08x ch20 0x%08x\n",
		    bo408, rd(bar0.base + 0x2cu), rd(bar0.base + 0x128), rd(bar0.base + 0x48),
		    rd(pcie_dma_extra + c408));
		if (bo408 == 0u || bo408 > 0x1000u) {
			printf("apply-408 a: bhioff looks wrong, using 0x100\n");
			bo408 = 0x100u;
		}
		printf("apply-408 b: before ver %08x/%08x imgaddr %08x/%08x size %08x db %08x\n",
		    rd(bar0.base + bo408 + 0x00u), rd(bar0.base + bo408 + 0x04u),
		    rd(bar0.base + bo408 + 0x08u), rd(bar0.base + bo408 + 0x0cu),
		    rd(bar0.base + bo408 + 0x10u), rd(bar0.base + bo408 + 0x18u));
		printf("apply-408 b: before intvec %08x execenv %08x status %08x errcode %08x\n",
		    rd(bar0.base + bo408 + 0x20u), rd(bar0.base + bo408 + 0x28u),
		    rd(bar0.base + bo408 + 0x2cu), rd(bar0.base + bo408 + 0x30u));
		printf("apply-408 b: before errdbg %08x %08x %08x serial %08x numseg %08x\n",
		    rd(bar0.base + bo408 + 0x34u), rd(bar0.base + bo408 + 0x38u),
		    rd(bar0.base + bo408 + 0x3cu), rd(bar0.base + bo408 + 0x40u),
		    rd(bar0.base + bo408 + 0x48u));

		/* START_CHAN(20): the reliable way to make the firmware assert */
		cwp408 = rd(pcie_dma_extra + 0x2400u + 0x24u);
		off408 = cwp408 - (uint32_t)PCIE_EXTRA_IOVA;
		wr(pcie_dma_extra + off408 + 0x00u, 0u);
		wr(pcie_dma_extra + off408 + 0x04u, 0u);
		wr(pcie_dma_extra + off408 + 0x08u, 0u);
		wr(pcie_dma_extra + off408 + 0x0cu, 0x14120000u);
		wr(pcie_dma_extra + 0x2400u + 0x24u, cwp408 + 16u);
		wr(bar0.base + 0x70u, cwp408 + 16u);
		printf("apply-408 c: START_CHAN(20) rung at 0x%08x\n", cwp408 + 16u);

		for (g408 = 0; g408 < 80u; g408++) {
			sleep_ms(5);
			ee408 = rd(bar0.base + 0x128);
			if (ee408 != 2u)
				break;
		}
		printf("apply-408 d: after %u ms ee 0x%08x mh 0x%08x ch20 0x%08x\n",
		    g408 * 5u, rd(bar0.base + 0x128), rd(bar0.base + 0x48),
		    rd(pcie_dma_extra + c408));

		printf("apply-408 e: ver %08x/%08x imgaddr %08x/%08x size %08x db %08x\n",
		    rd(bar0.base + bo408 + 0x00u), rd(bar0.base + bo408 + 0x04u),
		    rd(bar0.base + bo408 + 0x08u), rd(bar0.base + bo408 + 0x0cu),
		    rd(bar0.base + bo408 + 0x10u), rd(bar0.base + bo408 + 0x18u));
		printf("apply-408 e: intvec %08x execenv %08x status %08x errcode %08x\n",
		    rd(bar0.base + bo408 + 0x20u), rd(bar0.base + bo408 + 0x28u),
		    rd(bar0.base + bo408 + 0x2cu), rd(bar0.base + bo408 + 0x30u));
		printf("apply-408 e: errdbg %08x %08x %08x serial %08x numseg %08x\n",
		    rd(bar0.base + bo408 + 0x34u), rd(bar0.base + bo408 + 0x38u),
		    rd(bar0.base + bo408 + 0x3cu), rd(bar0.base + bo408 + 0x40u),
		    rd(bar0.base + bo408 + 0x48u));
		printf("apply-408 e: hwid0 %08x hwid1 %08x hwid2 %08x pkhash %08x %08x\n",
		    rd(bar0.base + bo408 + 0x4cu), rd(bar0.base + bo408 + 0x50u),
		    rd(bar0.base + bo408 + 0x54u), rd(bar0.base + bo408 + 0x64u),
		    rd(bar0.base + bo408 + 0x68u));
		printf("apply-408 f: same again after 100 ms\n");
		sleep_ms(100);
		printf("apply-408 f: status %08x errcode %08x errdbg %08x %08x %08x\n",
		    rd(bar0.base + bo408 + 0x2cu), rd(bar0.base + bo408 + 0x30u),
		    rd(bar0.base + bo408 + 0x34u), rd(bar0.base + bo408 + 0x38u),
		    rd(bar0.base + bo408 + 0x3cu));
		printf("apply-408 g: er0 %08x %08x | %08x %08x | %08x %08x | %08x %08x\n",
		    rd(pcie_dma_extra + 0x4000u), rd(pcie_dma_extra + 0x400cu),
		    rd(pcie_dma_extra + 0x4010u), rd(pcie_dma_extra + 0x401cu),
		    rd(pcie_dma_extra + 0x4020u), rd(pcie_dma_extra + 0x402cu),
		    rd(pcie_dma_extra + 0x4030u), rd(pcie_dma_extra + 0x403cu));
		printf("apply-408 h: er1 %08x %08x | %08x %08x | %08x %08x\n",
		    rd(pcie_dma_extra + 0x5000u), rd(pcie_dma_extra + 0x500cu),
		    rd(pcie_dma_extra + 0x5010u), rd(pcie_dma_extra + 0x501cu),
		    rd(pcie_dma_extra + 0x5020u), rd(pcie_dma_extra + 0x502cu));
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1
assert "apply-408" not in src

a = "pcie_mhi_data != 26u && pcie_mhi_data != 27u && pcie_mhi_data != 28u && pcie_chanstart != 0"
assert src.count(a) == 1, "gate A %d" % src.count(a)
src = src.replace(a, "pcie_mhi_data != 26u && pcie_mhi_data != 27u && pcie_mhi_data != 28u && pcie_mhi_data != 29u && pcie_chanstart != 0")
b = "pcie_mhi_data != 26u && pcie_mhi_data != 27u && pcie_mhi_data != 28u)"
assert src.count(b) == 1, "gate B %d" % src.count(b)
src = src.replace(b, "pcie_mhi_data != 26u && pcie_mhi_data != 27u && pcie_mhi_data != 28u && pcie_mhi_data != 29u)")

i = src.index(END)
src = src[:i] + BLOCK + src[i:]
assert src.count("apply-408 h") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-408 ok")
