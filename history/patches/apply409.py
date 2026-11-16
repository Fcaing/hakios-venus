#!/usr/bin/env python3
"""apply-409: read every event ring, not just the two we have been staring at.

MHICFG says NER=3, so the device has three event rings: er0 (control, 0x4000), er1 (irq /
IPCR, 0x5000) and er2 (bw-scale, 0x6000).  We have only ever dumped er0 and er1.  If the
firmware posted an SFR configuration request (MHI_PKT_TYPE_SFR_CFG_CMD 0x49) or a timesync
event (0x48) while it was booting, er2 is exactly where it would go - and nobody answered it,
which would explain why the firmware stops right after M0.

This round is read-only: dump 8 slots of each of the three rings with the type byte decoded,
the full ch20/ch21 contexts, and the MHICFG register.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-409: every event ring, and the channel contexts in full. */
	if (pcie_mhi_data == 30u && smmu_state == 1 && pcie_dma_extra != 0) {
		uint32_t e409, s409, o409, t409, m409;
		uint32_t cfg409 = rd(bar0.base + 0x10);

		printf("apply-409 a: cfg 0x%08x (nch %u nhwch %u ner %u nhwer %u) ee 0x%08x mh 0x%08x\n",
		    cfg409, cfg409 & 0xffu, (cfg409 >> 8) & 0xffu, (cfg409 >> 16) & 0xffu,
		    (cfg409 >> 24) & 0xffu, rd(bar0.base + 0x128), rd(bar0.base + 0x48));
		for (e409 = 0; e409 < 3u; e409++) {
			uint32_t cbase = pcie_dma_extra + 0x2000u + e409 * 0x2cu;
			uint32_t rb = rd(cbase + 0x0cu);

			printf("apply-409 b: er%u ctxt chstate 0x%08x eri 0x%08x rbase 0x%08x len 0x%08x rp 0x%08x wp 0x%08x\n",
			    e409, rd(cbase), rd(cbase + 0x08u), rb, rd(cbase + 0x14u),
			    rd(cbase + 0x1cu), rd(cbase + 0x24u));
			if (rb < (uint32_t)PCIE_EXTRA_IOVA || rb > (uint32_t)PCIE_EXTRA_IOVA + 0x500000u) {
				printf("apply-409 b: er%u rbase is outside the extra window, skipping\n", e409);
				continue;
			}
			o409 = rb - (uint32_t)PCIE_EXTRA_IOVA;
			for (s409 = 0; s409 < 8u; s409++) {
				uint32_t a = rd(pcie_dma_extra + o409 + s409 * 16u + 0x00u);
				uint32_t b = rd(pcie_dma_extra + o409 + s409 * 16u + 0x04u);
				uint32_t c = rd(pcie_dma_extra + o409 + s409 * 16u + 0x08u);
				uint32_t d = rd(pcie_dma_extra + o409 + s409 * 16u + 0x0cu);

				if ((a | b | c | d) == 0u)
					continue;
				t409 = (d >> 16) & 0xffu;
				m409 = c & 0xffffu;
				printf("apply-409 c: er%u[%u] %08x %08x %08x %08x type 0x%02x len 0x%04x ch %u\n",
				    e409, s409, a, b, c, d, t409, m409, d & 0xffu);
			}
		}
		printf("apply-409 d: ch20 %08x %08x %08x %08x %08x %08x %08x %08x\n",
		    rd(pcie_dma_extra + 20u * 0x2cu + 0x00u), rd(pcie_dma_extra + 20u * 0x2cu + 0x04u),
		    rd(pcie_dma_extra + 20u * 0x2cu + 0x08u), rd(pcie_dma_extra + 20u * 0x2cu + 0x0cu),
		    rd(pcie_dma_extra + 20u * 0x2cu + 0x14u), rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu),
		    rd(pcie_dma_extra + 20u * 0x2cu + 0x24u), rd(pcie_dma_extra + 20u * 0x2cu + 0x28u));
		printf("apply-409 d: ch21 %08x %08x %08x %08x %08x %08x %08x %08x\n",
		    rd(pcie_dma_extra + 21u * 0x2cu + 0x00u), rd(pcie_dma_extra + 21u * 0x2cu + 0x04u),
		    rd(pcie_dma_extra + 21u * 0x2cu + 0x08u), rd(pcie_dma_extra + 21u * 0x2cu + 0x0cu),
		    rd(pcie_dma_extra + 21u * 0x2cu + 0x14u), rd(pcie_dma_extra + 21u * 0x2cu + 0x1cu),
		    rd(pcie_dma_extra + 21u * 0x2cu + 0x24u), rd(pcie_dma_extra + 21u * 0x2cu + 0x28u));
		printf("apply-409 e: ch0 %08x %08x %08x %08x %08x %08x %08x %08x\n",
		    rd(pcie_dma_extra + 0x00u), rd(pcie_dma_extra + 0x04u),
		    rd(pcie_dma_extra + 0x08u), rd(pcie_dma_extra + 0x0cu),
		    rd(pcie_dma_extra + 0x14u), rd(pcie_dma_extra + 0x1cu),
		    rd(pcie_dma_extra + 0x24u), rd(pcie_dma_extra + 0x28u));
		printf("apply-409 f: wake db 0x%08x tsync 0x%08x bw 0x%08x\n",
		    rd(bar0.base + 0x300u + 8u * 127u + 0u),
		    rd(bar0.base + 0x300u + 8u * 126u + 0u),
		    rd(bar0.base + 0x300u + 8u * 125u + 0u));
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1
assert "apply-409" not in src

a = "pcie_mhi_data != 26u && pcie_mhi_data != 27u && pcie_mhi_data != 28u && pcie_mhi_data != 29u && pcie_chanstart != 0"
assert src.count(a) == 1, "gate A %d" % src.count(a)
src = src.replace(a, "pcie_mhi_data != 26u && pcie_mhi_data != 27u && pcie_mhi_data != 28u && pcie_mhi_data != 29u && pcie_mhi_data != 30u && pcie_chanstart != 0")
b = "pcie_mhi_data != 26u && pcie_mhi_data != 27u && pcie_mhi_data != 28u && pcie_mhi_data != 29u)"
assert src.count(b) == 1, "gate B %d" % src.count(b)
src = src.replace(b, "pcie_mhi_data != 26u && pcie_mhi_data != 27u && pcie_mhi_data != 28u && pcie_mhi_data != 29u && pcie_mhi_data != 30u)")

i = src.index(END)
src = src[:i] + BLOCK + src[i:]
assert src.count("apply-409 f") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-409 ok")
