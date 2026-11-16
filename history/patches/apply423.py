#!/usr/bin/env python3
"""apply-423: does the firmware create the IPCR channel contexts by itself?

Every round so far booted with pcie_chanstart=1, which writes ch20/ch21 contexts and sends
START_CHAN from the host.  So we have never seen what the firmware itself put there.  On a
real venus the debugfs `chan` node shows ch20/ch21 with the firmware's own rings
(0xa1e80000 / 0xa1e82000, len 0x200, wp advanced) - i.e. somebody on the device side created
them.  If our firmware never wrote those contexts, AMSS is not running its MHI client layer
at all, and the whole "why does ch20 not fetch" question collapses into "AMSS never started".

This probe is read-only and runs with pcie_chanstart=0, i.e. before anything in the driver
has touched a channel context.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-423: read-only.  What did the firmware put in the channel contexts? */
	if (pcie_mhi_data == 43u && smmu_state == 1 && pcie_dma_extra != 0) {
		uint32_t c423, o423;
		printf("apply-423 a: ee 0x%08x mh 0x%08x ctrl 0x%08x cfg 0x%08x chdboff 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(bar0.base + 0x38),
		    rd(bar0.base + 0x10), rd(bar0.base + 0x18));
		for (c423 = 0; c423 < 4u; c423++) {
			uint32_t ch423 = (c423 == 0u) ? 0u : ((c423 == 1u) ? 1u : ((c423 == 2u) ? 20u : 21u));
			o423 = ch423 * 0x2cu;
			printf("apply-423 ch%u: %08x %08x %08x %08x %08x %08x %08x %08x\n",
			    ch423,
			    rd(pcie_dma_extra + o423 + 0x00u), rd(pcie_dma_extra + o423 + 0x04u),
			    rd(pcie_dma_extra + o423 + 0x08u), rd(pcie_dma_extra + o423 + 0x0cu),
			    rd(pcie_dma_extra + o423 + 0x14u), rd(pcie_dma_extra + o423 + 0x1cu),
			    rd(pcie_dma_extra + o423 + 0x24u), rd(pcie_dma_extra + o423 + 0x28u));
		}
		printf("apply-423 b: er0 %08x %08x %08x | er1 %08x %08x %08x\n",
		    rd(pcie_dma_extra + 0x2000u + 0x1cu), rd(pcie_dma_extra + 0x2000u + 0x24u),
		    rd(pcie_dma_extra + 0x2000u + 0x0cu),
		    rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x1cu), rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x24u),
		    rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x0cu));
		printf("apply-423 c: ch20 doorbell 0x%08x ch21 doorbell 0x%08x wake 0x%08x\n",
		    rd(bar0.base + 0x300u + 20u * 8u), rd(bar0.base + 0x300u + 21u * 8u),
		    rd(bar0.base + 0x300u + 8u * 127u));
		sleep_ms(500);
		o423 = 20u * 0x2cu;
		printf("apply-423 d after 500 ms: ch20 %08x %08x %08x | ch21 %08x %08x %08x | ee 0x%08x\n",
		    rd(pcie_dma_extra + o423 + 0x00u), rd(pcie_dma_extra + o423 + 0x0cu),
		    rd(pcie_dma_extra + o423 + 0x24u),
		    rd(pcie_dma_extra + 21u * 0x2cu + 0x00u), rd(pcie_dma_extra + 21u * 0x2cu + 0x0cu),
		    rd(pcie_dma_extra + 21u * 0x2cu + 0x24u), rd(bar0.base + 0x128));
		printf("apply-423 done\n");
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1, "end marker"

a1 = "pcie_mhi_data != 42u && pcie_chanstart != 0"
a2 = "pcie_mhi_data != 42u) wr(pcie_dma_extra + 20 * 0x2c"
assert src.count(a1) == 1, "gate A anchor"
assert src.count(a2) == 1, "gate B anchor"
src = src.replace(a1, "pcie_mhi_data != 42u && pcie_mhi_data != 43u && pcie_chanstart != 0")
src = src.replace(a2, "pcie_mhi_data != 42u && pcie_mhi_data != 43u) wr(pcie_dma_extra + 20 * 0x2c")

assert "apply-423" not in src
a = src.index(END)
src = src[:a] + BLOCK + src[a:]
assert src.count("apply-423 done") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-423 ok")
