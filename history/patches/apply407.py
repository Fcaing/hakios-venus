#!/usr/bin/env python3
"""apply-407: the legal way to (re)start a channel - RESET_CHAN first, then START_CHAN.

p451 showed a bare START_CHAN(20) is poison: MHISTATUS jumps to 0xff05 (SYS_ERR) even when the
ring is the firmware's own.  The reason is almost certainly that ch20 is already RUNNING (the
SBL->AMSS handover left it there), and a second START is a protocol violation.  The vendor's
own path resets a channel before starting it:  MHI_PKT_TYPE_RESET_CHAN_CMD (0x10) then
MHI_PKT_TYPE_START_CHAN_CMD (0x12).  So: reset, wait for DISABLED, start, then put a good TRE
on the ring and see whether anything finally fetches it.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-407: RESET_CHAN(20) -> wait disabled -> START_CHAN(20) -> one good TRE. */
	if (pcie_mhi_data == 28u && smmu_state == 1 && pcie_dma_extra != 0 &&
	    rd(bar0.base + 0x128) == 2u) {
		uint32_t c20 = 20u * 0x2cu;
		uint32_t rb407 = rd(pcie_dma_extra + c20 + 0x0cu);
		uint32_t cwp407, off407, g407, ee407, st407, prev407;

		printf("apply-407 a: ee 0x%08x mh 0x%08x ch20 0x%08x ch21 0x%08x rbase 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48),
		    rd(pcie_dma_extra + c20), rd(pcie_dma_extra + 21u * 0x2cu), rb407);

		/* RESET_CHAN(20): word1 = (ch << 24) | (0x10 << 16) */
		cwp407 = rd(pcie_dma_extra + 0x2400u + 0x24u);
		off407 = cwp407 - (uint32_t)PCIE_EXTRA_IOVA;
		wr(pcie_dma_extra + off407 + 0x00u, 0u);
		wr(pcie_dma_extra + off407 + 0x04u, 0u);
		wr(pcie_dma_extra + off407 + 0x08u, 0u);
		wr(pcie_dma_extra + off407 + 0x0cu, 0x14100000u);
		wr(pcie_dma_extra + 0x2400u + 0x24u, cwp407 + 16u);
		wr(bar0.base + 0x70u, cwp407 + 16u);
		printf("apply-407 b: RESET_CHAN(20) rung at 0x%08x\n", cwp407 + 16u);

		prev407 = rd(pcie_dma_extra + c20);
		for (g407 = 0; g407 < 60u; g407++) {
			sleep_ms(5);
			st407 = rd(pcie_dma_extra + c20);
			if ((st407 & 0xffu) != (prev407 & 0xffu))
				break;
		}
		printf("apply-407 c: after reset %u ms ch20 0x%08x ee 0x%08x mh 0x%08x\n",
		    g407 * 5u, rd(pcie_dma_extra + c20), rd(bar0.base + 0x128), rd(bar0.base + 0x48));

		/* START_CHAN(20): word1 = (ch << 24) | (0x12 << 16) */
		cwp407 = rd(pcie_dma_extra + 0x2400u + 0x24u);
		off407 = cwp407 - (uint32_t)PCIE_EXTRA_IOVA;
		wr(pcie_dma_extra + off407 + 0x00u, 0u);
		wr(pcie_dma_extra + off407 + 0x04u, 0u);
		wr(pcie_dma_extra + off407 + 0x08u, 0u);
		wr(pcie_dma_extra + off407 + 0x0cu, 0x14120000u);
		wr(pcie_dma_extra + 0x2400u + 0x24u, cwp407 + 16u);
		wr(bar0.base + 0x70u, cwp407 + 16u);
		printf("apply-407 d: START_CHAN(20) rung at 0x%08x\n", cwp407 + 16u);

		prev407 = rd(pcie_dma_extra + c20);
		for (g407 = 0; g407 < 60u; g407++) {
			sleep_ms(5);
			st407 = rd(pcie_dma_extra + c20);
			if ((st407 & 0xffu) != (prev407 & 0xffu))
				break;
		}
		printf("apply-407 e: after start %u ms ch20 0x%08x ee 0x%08x mh 0x%08x\n",
		    g407 * 5u, rd(pcie_dma_extra + c20), rd(bar0.base + 0x128), rd(bar0.base + 0x48));

		/* finally a good TRE on the firmware's own ring */
		if (rb407 >= (uint32_t)PCIE_EXTRA_IOVA && rb407 < (uint32_t)PCIE_EXTRA_IOVA + 0x500000u) {
			off407 = rb407 - (uint32_t)PCIE_EXTRA_IOVA;
			wr(pcie_dma_extra + off407 + 0x00u, (uint32_t)(PCIE_EXTRA_IOVA + 0x3a0000u));
			wr(pcie_dma_extra + off407 + 0x04u, 0u);
			wr(pcie_dma_extra + off407 + 0x08u, 0x00000010u);
			wr(pcie_dma_extra + off407 + 0x0cu, 0x00020200u);
			wr(pcie_dma_extra + 0x3a0000u + 0x0u, 0x5241514bu);
			wr(pcie_dma_extra + 0x3a0000u + 0x4u, 0x4d495451u);
			wr(pcie_dma_extra + c20 + 0x1cu, rb407);
			wr(pcie_dma_extra + c20 + 0x24u, rb407 + 16u);
			wr(bar0.base + 0x300u + 20u * 8u + 4u, 0u);
			wr(bar0.base + 0x300u + 20u * 8u, rb407 + 16u);
			printf("apply-407 f: tre queued at 0x%08x, doorbell 0x%08x\n", rb407, rb407 + 16u);
		}
		prev407 = rd(pcie_dma_extra + c20);
		for (g407 = 0; g407 < 100u; g407++) {
			sleep_ms(5);
			st407 = rd(pcie_dma_extra + c20);
			ee407 = rd(bar0.base + 0x128);
			if ((st407 & 0xffu) != (prev407 & 0xffu) || ee407 != 2u)
				break;
		}
		printf("apply-407 g: waited %u ms ch20 0x%08x rp 0x%08x wp 0x%08x ee 0x%08x mh 0x%08x\n",
		    g407 * 5u, rd(pcie_dma_extra + c20),
		    rd(pcie_dma_extra + c20 + 0x1cu), rd(pcie_dma_extra + c20 + 0x24u),
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48));
		printf("apply-407 h: er0 %08x %08x | %08x %08x | %08x %08x | %08x %08x\n",
		    rd(pcie_dma_extra + 0x4000u), rd(pcie_dma_extra + 0x400cu),
		    rd(pcie_dma_extra + 0x4010u), rd(pcie_dma_extra + 0x401cu),
		    rd(pcie_dma_extra + 0x4020u), rd(pcie_dma_extra + 0x402cu),
		    rd(pcie_dma_extra + 0x4030u), rd(pcie_dma_extra + 0x403cu));
		printf("apply-407 i: er1 %08x %08x | %08x %08x | %08x %08x\n",
		    rd(pcie_dma_extra + 0x5000u), rd(pcie_dma_extra + 0x500cu),
		    rd(pcie_dma_extra + 0x5010u), rd(pcie_dma_extra + 0x501cu),
		    rd(pcie_dma_extra + 0x5020u), rd(pcie_dma_extra + 0x502cu));
		printf("apply-407 j: bhi status 0x%08x errcode 0x%08x\n",
		    rd(bar0.base + 0x12cu), rd(bar0.base + 0x130u));
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1
assert "apply-407" not in src

a = "pcie_mhi_data != 26u && pcie_mhi_data != 27u && pcie_chanstart != 0"
assert src.count(a) == 1, "gate A %d" % src.count(a)
src = src.replace(a, "pcie_mhi_data != 26u && pcie_mhi_data != 27u && pcie_mhi_data != 28u && pcie_chanstart != 0")
b = "pcie_mhi_data != 26u && pcie_mhi_data != 27u)"
assert src.count(b) == 1, "gate B %d" % src.count(b)
src = src.replace(b, "pcie_mhi_data != 26u && pcie_mhi_data != 27u && pcie_mhi_data != 28u)")

i = src.index(END)
src = src[:i] + BLOCK + src[i:]
assert src.count("apply-407 j") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-407 ok")
