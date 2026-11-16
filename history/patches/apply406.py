#!/usr/bin/env python3
"""apply-406: keep the firmware's own ch20 ring, put a TRE there, then START_CHAN again.

p450 isolated the failure: rewriting ch20's context (rbase 0xa0208000) and then sending
START_CHAN(20) drives EE 2 -> 3 with MHISTATUS 0x0000ff05 (MHISTATE 0xff + SYSERR).  Rewriting
the context alone is harmless, so the firmware is checking something at START_CHAN time - most
likely that the ring it was told about is not the ring it owns (0xa020c000).

So this round does not touch rbase.  It writes one TX TRE into 0xa020c000, sets wp = rp + 16,
sends START_CHAN(20) at a forward cmd wp, and watches EE, ch20 and both event rings.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-406: the firmware's own ring, one good TRE, one more START_CHAN. */
	if (pcie_mhi_data == 27u && smmu_state == 1 && pcie_dma_extra != 0 &&
	    rd(bar0.base + 0x128) == 2u) {
		uint32_t c20 = 20u * 0x2cu;
		uint32_t rb406 = rd(pcie_dma_extra + c20 + 0x0cu);
		uint32_t ln406 = rd(pcie_dma_extra + c20 + 0x14u);
		uint32_t rp406 = rd(pcie_dma_extra + c20 + 0x1cu);
		uint32_t wp406 = rd(pcie_dma_extra + c20 + 0x24u);
		uint32_t cwp406 = rd(pcie_dma_extra + 0x2400u + 0x24u);
		uint32_t off406, g406, ee406, st406;

		printf("apply-406 a: ee 0x%08x mh 0x%08x ch20 st 0x%08x rbase 0x%08x len 0x%08x rp 0x%08x wp 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(pcie_dma_extra + c20),
		    rb406, ln406, rp406, wp406);
		printf("apply-406 b: cmd wp 0x%08x\n", cwp406);

		if (rb406 >= (uint32_t)PCIE_EXTRA_IOVA && rb406 < (uint32_t)PCIE_EXTRA_IOVA + 0x500000u) {
			off406 = rb406 - (uint32_t)PCIE_EXTRA_IOVA;
			/* one TX TRE at the ring head: 16 bytes of payload we own */
			wr(pcie_dma_extra + off406 + 0x00u, (uint32_t)(PCIE_EXTRA_IOVA + 0x3a0000u));
			wr(pcie_dma_extra + off406 + 0x04u, 0u);
			wr(pcie_dma_extra + off406 + 0x08u, 0x00000010u);
			wr(pcie_dma_extra + off406 + 0x0cu, 0x00020200u);
			wr(pcie_dma_extra + 0x3a0000u + 0x0u, 0x5241514bu);	/* "KQAR" */
			wr(pcie_dma_extra + 0x3a0000u + 0x4u, 0x4d495451u);
			wr(pcie_dma_extra + 0x3a0000u + 0x8u, 0x00000000u);
			wr(pcie_dma_extra + 0x3a0000u + 0xcu, 0x00000000u);
			/* rp stays, wp moves one element forward */
			wr(pcie_dma_extra + c20 + 0x1cu, rb406);
			wr(pcie_dma_extra + c20 + 0x24u, rb406 + 16u);
			printf("apply-406 c: tre at 0xa%06x -> payload 0xa%06x, wp 0x%08x\n",
			    (unsigned)(rb406 & 0xffffffu), 0x3a0000u, rb406 + 16u);
		} else {
			printf("apply-406 c: rbase 0x%08x is outside the extra window\n", rb406);
		}

		/* START_CHAN(20) at a forward cmd wp, leaving the ring itself alone */
		wr(pcie_dma_extra + 0x2400u + 0x0cu + (cwp406 - (uint32_t)PCIE_EXTRA_IOVA - 0x7000u), 0x14120000u);
		wr(pcie_dma_extra + 0x2400u + 0x24u, cwp406 + 16u);
		wr(bar0.base + 0x70u, cwp406 + 16u);
		printf("apply-406 d: start20 rung, cmd wp 0x%08x\n", cwp406 + 16u);

		for (g406 = 0; g406 < 60u; g406++) {
			sleep_ms(5);
			ee406 = rd(bar0.base + 0x128);
			st406 = rd(pcie_dma_extra + c20);
			if (ee406 != 2u || (st406 & 0xffu) != 1u)
				break;
		}
		printf("apply-406 e: waited %u ms ee 0x%08x mh 0x%08x ch20 0x%08x rp 0x%08x wp 0x%08x\n",
		    g406 * 5u, rd(bar0.base + 0x128), rd(bar0.base + 0x48),
		    rd(pcie_dma_extra + c20),
		    rd(pcie_dma_extra + c20 + 0x1cu), rd(pcie_dma_extra + c20 + 0x24u));
		printf("apply-406 f: er0 %08x %08x | %08x %08x | %08x %08x | %08x %08x\n",
		    rd(pcie_dma_extra + 0x4000u), rd(pcie_dma_extra + 0x400cu),
		    rd(pcie_dma_extra + 0x4010u), rd(pcie_dma_extra + 0x401cu),
		    rd(pcie_dma_extra + 0x4020u), rd(pcie_dma_extra + 0x402cu),
		    rd(pcie_dma_extra + 0x4030u), rd(pcie_dma_extra + 0x403cu));
		printf("apply-406 g: er1 %08x %08x | %08x %08x\n",
		    rd(pcie_dma_extra + 0x5000u), rd(pcie_dma_extra + 0x500cu),
		    rd(pcie_dma_extra + 0x5010u), rd(pcie_dma_extra + 0x501cu));
		printf("apply-406 h: errcode-ish 0x%08x 0x%08x smmu gfsr 0x%08x\n",
		    rd(bar0.base + 0x130u), rd(bar0.base + 0x12cu),
		    smmu_state == 1 ? rd(smmu_mmio + 0x48u) : 0u);
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1
assert "apply-406" not in src

a = "pcie_mhi_data != 24u && pcie_mhi_data != 25u && pcie_mhi_data != 26u && pcie_chanstart != 0"
assert src.count(a) == 1, "gate A %d" % src.count(a)
src = src.replace(a, "pcie_mhi_data != 24u && pcie_mhi_data != 25u && pcie_mhi_data != 26u && pcie_mhi_data != 27u && pcie_chanstart != 0")
b = "pcie_mhi_data != 24u && pcie_mhi_data != 25u && pcie_mhi_data != 26u)"
assert src.count(b) == 1, "gate B %d" % src.count(b)
src = src.replace(b, "pcie_mhi_data != 24u && pcie_mhi_data != 25u && pcie_mhi_data != 26u && pcie_mhi_data != 27u)")

i = src.index(END)
src = src[:i] + BLOCK + src[i:]
assert src.count("apply-406 h") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-406 ok")
