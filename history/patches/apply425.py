#!/usr/bin/env python3
"""apply-425: the one transition we never tried with the firmware's own contexts - M0 -> M2.

Every earlier M2 attempt (p448, p462) ran with pcie_chanstart=1, i.e. after the host had
rewritten the channel contexts and STARTed them.  The device on the real phone idles in M2
(MHI_CNTRL 0x400 / MHI_STATUS 0x401) and only comes back to M0 when traffic flows.  Ours
never leaves M0.  So: leave the contexts alone, settle, ask for M2, and see whether the
firmware finally agrees.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-425: pristine contexts, then ask for M2 and watch. */
	if (pcie_mhi_data == 45u && smmu_state == 1 && pcie_dma_extra != 0 &&
	    rd(bar0.base + 0x128) == 2u) {
		uint32_t k425, mh425, st425, wp425, tre425off;
		vm_offset_t tre425;

		printf("apply-425 a: before m2 ee 0x%08x mh 0x%08x ctrl 0x%08x ch20 0x%08x ch21 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(bar0.base + 0x38),
		    rd(pcie_dma_extra + 20u * 0x2cu), rd(pcie_dma_extra + 21u * 0x2cu));
		sleep_ms(2000);
		mh425 = rd(bar0.base + 0x48);
		printf("apply-425 b: settled mh 0x%08x ch20 0x%08x wp 0x%08x\n",
		    mh425, rd(pcie_dma_extra + 20u * 0x2cu), rd(pcie_dma_extra + 20u * 0x2cu + 0x24u));
		wr(bar0.base + 0x38, 0x00000400u);	/* MHICTRL <- M2 */
		for (k425 = 0; k425 < 100u; k425++) {
			sleep_ms(10);
			if (rd(bar0.base + 0x48) != mh425) {
				printf("apply-425 c: t=%u ms mh 0x%08x ctrl 0x%08x ee 0x%08x\n",
				    k425 * 10u, rd(bar0.base + 0x48), rd(bar0.base + 0x38), rd(bar0.base + 0x128));
				break;
			}
		}
		printf("apply-425 d: after m2 mh 0x%08x ctrl 0x%08x ee 0x%08x ch20 0x%08x ch21 0x%08x\n",
		    rd(bar0.base + 0x48), rd(bar0.base + 0x38), rd(bar0.base + 0x128),
		    rd(pcie_dma_extra + 20u * 0x2cu), rd(pcie_dma_extra + 21u * 0x2cu));
		/* in whatever state we are now, hand the firmware one tre and ring */
		st425 = rd(pcie_dma_extra + 20u * 0x2cu);
		wp425 = rd(pcie_dma_extra + 20u * 0x2cu + 0x24u);
		if (wp425 >= (uint32_t)PCIE_EXTRA_IOVA && wp425 < (uint32_t)(PCIE_EXTRA_IOVA + 0x100000u)) {
			tre425off = wp425 - (uint32_t)PCIE_EXTRA_IOVA;
			tre425 = pcie_dma_extra + tre425off;
			wr(tre425 + 0x00u, (uint32_t)(PCIE_EXTRA_IOVA + 0x3a0000u));
			wr(tre425 + 0x04u, 0u);
			wr(tre425 + 0x08u, 0x00000020u);
			wr(tre425 + 0x0cu, 0x00020200u);
			__asm__ __volatile__("dc civac, %0" :: "r"(tre425) : "memory");
			__asm__ __volatile__("dsb sy" ::: "memory");
			wr(bar0.base + 0x300u + 20u * 8u + 4u, 0u);
			wr(bar0.base + 0x300u + 20u * 8u, wp425 + 0x10u);
			printf("apply-425 e: tre at 0x%llx rung 0x3a0 <- 0x%08x (ch20 st 0x%08x)\n",
			    (unsigned long long)tre425, wp425 + 0x10u, st425);
		}
		for (k425 = 0; k425 < 50u; k425++) {
			sleep_ms(10);
			if (rd(pcie_dma_extra + 20u * 0x2cu) != st425 ||
			    rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu) != rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu)) {
				printf("apply-425 f: t=%u ms ch20 0x%08x rp 0x%08x wp 0x%08x ee 0x%08x mh 0x%08x\n",
				    k425 * 10u, rd(pcie_dma_extra + 20u * 0x2cu),
				    rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu), rd(pcie_dma_extra + 20u * 0x2cu + 0x24u),
				    rd(bar0.base + 0x128), rd(bar0.base + 0x48));
				break;
			}
		}
		printf("apply-425 g: end mh 0x%08x ctrl 0x%08x ee 0x%08x ch20 0x%08x rp 0x%08x wp 0x%08x\n",
		    rd(bar0.base + 0x48), rd(bar0.base + 0x38), rd(bar0.base + 0x128),
		    rd(pcie_dma_extra + 20u * 0x2cu), rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu),
		    rd(pcie_dma_extra + 20u * 0x2cu + 0x24u));
		printf("apply-425 done\n");
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1, "end marker"
assert "apply-425" not in src

a1 = "pcie_mhi_data != 43u && pcie_mhi_data != 44u && pcie_chanstart != 0"
a2 = "pcie_mhi_data != 43u && pcie_mhi_data != 44u) wr(pcie_dma_extra + 20 * 0x2c"
assert src.count(a1) == 1, "gate A"
assert src.count(a2) == 1, "gate B"
src = src.replace(a1, "pcie_mhi_data != 43u && pcie_mhi_data != 44u && pcie_mhi_data != 45u && pcie_chanstart != 0")
src = src.replace(a2, "pcie_mhi_data != 43u && pcie_mhi_data != 44u && pcie_mhi_data != 45u) wr(pcie_dma_extra + 20 * 0x2c")

a = src.index(END)
src = src[:a] + BLOCK + src[a:]
assert src.count("apply-425 done") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-425 ok")
