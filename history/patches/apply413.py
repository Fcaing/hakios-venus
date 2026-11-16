#!/usr/bin/env python3
"""apply-413: the one host action we never did -- a real MHICTRL reset before boot.

cnss2's power-on path starts from MHI_PM_POR, which writes MHISTATE=RESET (MHICTRL bit 1)
and waits for the device to acknowledge before it ever touches BHI.  Every round we have
run started from whatever state the SBL left behind instead.

So: write the reset bit before the download, watch EE/MHISTATUS for up to two seconds,
clear it, then let the normal flow continue.  At the end dump the three event rings and the
channel contexts so this round can be compared byte for byte with p455.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"
ANCHOR = "\tprintf(\"apply-402 reach: mhi_data %u smmu %u dma 0x%llx ee 0x%08x\\n\",\n"

PRE = r'''	if (pcie_mhi_data == 33u && pcie_dma_extra != 0) {
		uint32_t k413, ee413, mh413, ctrl413;

		ee413 = rd(bar0.base + 0x128);
		mh413 = rd(bar0.base + 0x48);
		ctrl413 = rd(bar0.base + 0x38);
		printf("apply-413 a: before reset ee 0x%08x mh 0x%08x ctrl 0x%08x\n", ee413, mh413, ctrl413);
		wr(bar0.base + 0x38, ctrl413 | 0x00000002u);
		for (k413 = 0; k413 < 40u; k413++) {
			sleep_ms(50);
			if (rd(bar0.base + 0x128) != ee413 ||
			    (rd(bar0.base + 0x48) & 0xffu) != (mh413 & 0xffu)) {
				printf("apply-413 b: t=%u ms ee 0x%08x mh 0x%08x ctrl 0x%08x\n",
				    k413 * 50u + 50u, rd(bar0.base + 0x128), rd(bar0.base + 0x48),
				    rd(bar0.base + 0x38));
				break;
			}
		}
		wr(bar0.base + 0x38, rd(bar0.base + 0x38) & ~0x00000002u);
		printf("apply-413 c: after reset ee 0x%08x mh 0x%08x ctrl 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(bar0.base + 0x38));
	}

'''

POST = r'''	/* apply-413: same dump as p455, so the two rounds can be diffed. */
	if (pcie_mhi_data == 33u && smmu_state == 1 && pcie_dma_extra != 0) {
		uint32_t e413;

		printf("apply-413 d: ee 0x%08x mh 0x%08x ch20 0x%08x ch21 0x%08x ch0 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48),
		    rd(pcie_dma_extra + 20u * 0x2cu), rd(pcie_dma_extra + 21u * 0x2cu),
		    rd(pcie_dma_extra));
		for (e413 = 0; e413 < 3u; e413++) {
			uint32_t cofs413 = 0x2000u + e413 * 0x2cu;
			uint32_t rofs413 = 0x4000u + e413 * 0x1000u;
			uint32_t j413;

			printf("apply-413 er%u ctxt rbase 0x%08x len 0x%08x rp 0x%08x wp 0x%08x\n",
			    e413, rd(pcie_dma_extra + cofs413 + 0x0cu), rd(pcie_dma_extra + cofs413 + 0x14u),
			    rd(pcie_dma_extra + cofs413 + 0x1cu), rd(pcie_dma_extra + cofs413 + 0x24u));
			for (j413 = 0; j413 < 6u; j413++)
				printf("apply-413 er%u[%u] %08x %08x %08x %08x\n", e413, j413,
				    rd(pcie_dma_extra + rofs413 + j413 * 16u + 0u),
				    rd(pcie_dma_extra + rofs413 + j413 * 16u + 4u),
				    rd(pcie_dma_extra + rofs413 + j413 * 16u + 8u),
				    rd(pcie_dma_extra + rofs413 + j413 * 16u + 12u));
		}
		printf("apply-413 e: ch20 %08x %08x %08x %08x %08x %08x %08x\n",
		    rd(pcie_dma_extra + 20u * 0x2cu + 0x00u), rd(pcie_dma_extra + 20u * 0x2cu + 0x04u),
		    rd(pcie_dma_extra + 20u * 0x2cu + 0x08u), rd(pcie_dma_extra + 20u * 0x2cu + 0x0cu),
		    rd(pcie_dma_extra + 20u * 0x2cu + 0x14u), rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu),
		    rd(pcie_dma_extra + 20u * 0x2cu + 0x24u));
		printf("apply-413 f: ch21 %08x %08x %08x %08x %08x %08x %08x\n",
		    rd(pcie_dma_extra + 21u * 0x2cu + 0x00u), rd(pcie_dma_extra + 21u * 0x2cu + 0x04u),
		    rd(pcie_dma_extra + 21u * 0x2cu + 0x08u), rd(pcie_dma_extra + 21u * 0x2cu + 0x0cu),
		    rd(pcie_dma_extra + 21u * 0x2cu + 0x14u), rd(pcie_dma_extra + 21u * 0x2cu + 0x1cu),
		    rd(pcie_dma_extra + 21u * 0x2cu + 0x24u));
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1
assert "apply-413" not in src
assert src.count(ANCHOR) == 1, "anchor %d" % src.count(ANCHOR)

# gate the two legacy writers off for this probe as well
a = "pcie_mhi_data != 30u && pcie_mhi_data != 32u && pcie_chanstart != 0"
assert src.count(a) == 1
src = src.replace(a, "pcie_mhi_data != 30u && pcie_mhi_data != 32u && pcie_mhi_data != 33u && pcie_chanstart != 0")
b = "pcie_mhi_data != 30u && pcie_mhi_data != 32u) wr(pcie_dma_extra + 20 * 0x2c"
assert src.count(b) == 1
src = src.replace(b, "pcie_mhi_data != 30u && pcie_mhi_data != 32u && pcie_mhi_data != 33u) wr(pcie_dma_extra + 20 * 0x2c")

i = src.index(ANCHOR)
src = src[:i] + PRE + src[i:]
j = src.index(END)
src = src[:j] + POST + src[j:]
assert src.count("apply-413 e:") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-413 ok")
