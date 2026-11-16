#!/usr/bin/env python3
"""apply-405: isolate which step pushes the firmware into RDDM.

p449 proved the IPCR channels are not inert: rewriting their contexts, sending
START_CHAN to both, laying 32 RX TREs on ch21 and pushing a QRTR hello on ch20
moved EE from 2 to 3 (RDDM).  That is the first time a data-plane action (not
0xb0) changed the firmware's state.  Now split it into five steps and watch EE,
er0 and er1 after each one.  Fixes from p449: the event *ring* lives at +0x4000
(er0) and +0x5000 (er1), not at +0x2000 (that is the context array); and the
change detector stores its initial value instead of comparing rp against wp.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-405: which step makes the firmware leave AMSS for RDDM? */
	if (pcie_mhi_data == 26u && smmu_state == 1 && pcie_dma_extra != 0 &&
	    rd(bar0.base + 0x128) == 2u) {
		uint32_t g405, ee405, st405;
		uint32_t c20 = 20u * 0x2cu, c21 = 21u * 0x2cu;

		printf("apply-405 s0: ee 0x%08x mh 0x%08x ch20 0x%08x ch21 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48),
		    rd(pcie_dma_extra + c20), rd(pcie_dma_extra + c21));

		/* step 1: rewrite both contexts the way star does */
		wr(pcie_dma_extra + c20 + 0x00u, 0x201u);
		wr(pcie_dma_extra + c20 + 0x04u, 1u);
		wr(pcie_dma_extra + c20 + 0x08u, 1u);
		wr(pcie_dma_extra + c20 + 0x0cu, (uint32_t)(PCIE_EXTRA_IOVA + 0x8000u));
		wr(pcie_dma_extra + c20 + 0x14u, 32u * 16u);
		wr(pcie_dma_extra + c20 + 0x1cu, (uint32_t)(PCIE_EXTRA_IOVA + 0x8000u));
		wr(pcie_dma_extra + c20 + 0x24u, (uint32_t)(PCIE_EXTRA_IOVA + 0x8000u));
		wr(pcie_dma_extra + c21 + 0x00u, 0x201u);
		wr(pcie_dma_extra + c21 + 0x04u, 2u);
		wr(pcie_dma_extra + c21 + 0x08u, 1u);
		wr(pcie_dma_extra + c21 + 0x0cu, (uint32_t)(PCIE_EXTRA_IOVA + 0x9000u));
		wr(pcie_dma_extra + c21 + 0x14u, 32u * 16u);
		wr(pcie_dma_extra + c21 + 0x1cu, (uint32_t)(PCIE_EXTRA_IOVA + 0x9000u));
		wr(pcie_dma_extra + c21 + 0x24u, (uint32_t)(PCIE_EXTRA_IOVA + 0x9000u));
		sleep_ms(2);
		printf("apply-405 s1 ctx: ch20 0x%08x ch21 0x%08x ee 0x%08x\n",
		    rd(pcie_dma_extra + c20), rd(pcie_dma_extra + c21), rd(bar0.base + 0x128));

		/* step 2: START_CHAN(20) only */
		wr(pcie_dma_extra + 0x2400u + 0x00u, 0u);
		wr(pcie_dma_extra + 0x2400u + 0x04u, 0u);
		wr(pcie_dma_extra + 0x2400u + 0x08u, 0u);
		wr(pcie_dma_extra + 0x2400u + 0x0cu, 0x14120000u);
		wr(pcie_dma_extra + 0x2400u + 0x24u, (uint32_t)(PCIE_EXTRA_IOVA + 0x7010u));
		wr(bar0.base + 0x70u, (uint32_t)(PCIE_EXTRA_IOVA + 0x7010u));
		for (g405 = 0; g405 < 40u; g405++) {
			sleep_ms(5);
			if (rd(bar0.base + 0x128) != 2u)
				break;
		}
		printf("apply-405 s2 start20: waited %u ms ee 0x%08x mh 0x%08x ch20 0x%08x\n",
		    g405 * 5u, rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(pcie_dma_extra + c20));
		printf("apply-405 s2 er0: %08x %08x %08x %08x | %08x %08x %08x %08x\n",
		    rd(pcie_dma_extra + 0x4000u), rd(pcie_dma_extra + 0x400cu),
		    rd(pcie_dma_extra + 0x4010u), rd(pcie_dma_extra + 0x401cu),
		    rd(pcie_dma_extra + 0x4020u), rd(pcie_dma_extra + 0x402cu),
		    rd(pcie_dma_extra + 0x4030u), rd(pcie_dma_extra + 0x403cu));

		/* step 3: START_CHAN(21) */
		wr(pcie_dma_extra + 0x2400u + 0x0cu, 0x14130000u);
		wr(pcie_dma_extra + 0x2400u + 0x24u, (uint32_t)(PCIE_EXTRA_IOVA + 0x7020u));
		wr(bar0.base + 0x70u, (uint32_t)(PCIE_EXTRA_IOVA + 0x7020u));
		sleep_ms(50);
		printf("apply-405 s3 start21: ee 0x%08x ch21 0x%08x\n",
		    rd(bar0.base + 0x128), rd(pcie_dma_extra + c21));

		/* step 4: 32 RX TREs on ch21, buffers well inside the extra window */
		for (g405 = 0; g405 < 32u; g405++) {
			uint32_t o = 0x9000u + g405 * 16u;
			wr(pcie_dma_extra + o + 0x0u, (uint32_t)(PCIE_EXTRA_IOVA + 0x300000u + g405 * 0x8000u));
			wr(pcie_dma_extra + o + 0x4u, 0u);
			wr(pcie_dma_extra + o + 0x8u, 0x00008000u);
			wr(pcie_dma_extra + o + 0xcu, 0x00020200u);
		}
		wr(pcie_dma_extra + c21 + 0x24u, (uint32_t)(PCIE_EXTRA_IOVA + 0x9000u + 31u * 16u));
		wr(bar0.base + 0x300u + 21u * 8u + 4u, 0u);
		wr(bar0.base + 0x300u + 21u * 8u, (uint32_t)(PCIE_EXTRA_IOVA + 0x9000u + 31u * 16u));
		sleep_ms(50);
		printf("apply-405 s4 rx: ee 0x%08x ch21 0x%08x\n",
		    rd(bar0.base + 0x128), rd(pcie_dma_extra + c21));

		/* step 5: one QRTR hello on ch20 */
		wr(pcie_dma_extra + (0x8000u - 0x0u) + 0x0u, 0x00000001u);
		wr(pcie_dma_extra + 0x8000u + 0x4u, 0x00000002u);
		wr(pcie_dma_extra + 0x8000u + 0x8u, 0x00000001u);
		wr(pcie_dma_extra + 0x8000u + 0xcu, 0xfffffffeu);
		wr(pcie_dma_extra + 0x8000u + 0x10u, 0x00000000u);
		wr(pcie_dma_extra + 0x8000u + 0x14u, 0x00000014u);
		wr(pcie_dma_extra + 0x8000u + 0x18u, 0x00000001u);
		wr(pcie_dma_extra + 0x8000u + 0x1cu, 0xfffffffeu);
		wr(pcie_dma_extra + 0x8000u + 0x20u, 0x00000002u);
		wr(pcie_dma_extra + 0x8000u + 0x24u, 0x00000000u);
		wr(pcie_dma_extra + 0x8010u + 0x0u, (uint32_t)(PCIE_EXTRA_IOVA + 0x8000u));
		wr(pcie_dma_extra + 0x8010u + 0x4u, 0u);
		wr(pcie_dma_extra + 0x8010u + 0x8u, 0x00000028u);
		wr(pcie_dma_extra + 0x8010u + 0xcu, 0x00020200u);
		wr(pcie_dma_extra + c20 + 0x24u, (uint32_t)(PCIE_EXTRA_IOVA + 0x8010u));
		wr(bar0.base + 0x300u + 20u * 8u + 4u, 0u);
		wr(bar0.base + 0x300u + 20u * 8u, (uint32_t)(PCIE_EXTRA_IOVA + 0x8010u));
		for (g405 = 0; g405 < 60u; g405++) {
			sleep_ms(5);
			ee405 = rd(bar0.base + 0x128);
			st405 = rd(pcie_dma_extra + c20);
			if (ee405 != 2u || (st405 & 0xffu) != 1u)
				break;
		}
		printf("apply-405 s5 hello: waited %u ms ee 0x%08x ch20 0x%08x ch21 0x%08x\n",
		    g405 * 5u, rd(bar0.base + 0x128), rd(pcie_dma_extra + c20), rd(pcie_dma_extra + c21));
		printf("apply-405 z er0: %08x %08x %08x %08x | %08x %08x %08x %08x\n",
		    rd(pcie_dma_extra + 0x4000u), rd(pcie_dma_extra + 0x400cu),
		    rd(pcie_dma_extra + 0x4010u), rd(pcie_dma_extra + 0x401cu),
		    rd(pcie_dma_extra + 0x4020u), rd(pcie_dma_extra + 0x402cu),
		    rd(pcie_dma_extra + 0x4030u), rd(pcie_dma_extra + 0x403cu));
		printf("apply-405 z er1: %08x %08x %08x %08x | %08x %08x %08x %08x\n",
		    rd(pcie_dma_extra + 0x5000u), rd(pcie_dma_extra + 0x500cu),
		    rd(pcie_dma_extra + 0x5010u), rd(pcie_dma_extra + 0x501cu),
		    rd(pcie_dma_extra + 0x5020u), rd(pcie_dma_extra + 0x502cu),
		    rd(pcie_dma_extra + 0x5030u), rd(pcie_dma_extra + 0x503cu));
		printf("apply-405 z rx0: %08x %08x %08x %08x\n",
		    rd(pcie_dma_extra + 0x300000u), rd(pcie_dma_extra + 0x300004u),
		    rd(pcie_dma_extra + 0x300008u), rd(pcie_dma_extra + 0x30000cu));
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1
assert "apply-405" not in src

a = "pcie_mhi_data != 24u && pcie_mhi_data != 25u && pcie_chanstart != 0"
assert src.count(a) == 1, "gate A count %d" % src.count(a)
src = src.replace(a, "pcie_mhi_data != 24u && pcie_mhi_data != 25u && pcie_mhi_data != 26u && pcie_chanstart != 0")
b = "pcie_mhi_data != 24u && pcie_mhi_data != 25u)"
assert src.count(b) == 1, "gate B count %d" % src.count(b)
src = src.replace(b, "pcie_mhi_data != 24u && pcie_mhi_data != 25u && pcie_mhi_data != 26u)")

i = src.index(END)
src = src[:i] + BLOCK + src[i:]
assert src.count("apply-405 z rx0") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-405 ok")
