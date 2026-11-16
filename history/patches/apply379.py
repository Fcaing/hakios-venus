#!/usr/bin/env python3
"""apply-379: the fetch question.

Dumps every event ring slot in full (16 bytes, not just dword0), rings the
command and ch20 doorbells once, and watches the SMMU fault registers the
whole time.

Why: "the device never consumed a command TRE" has two very different causes
and we cannot tell them apart yet.
  (a) the MHI engine never fetched -> the doorbell or the engine is dead
  (b) the engine fetched and the translation refused it -> an smmu fault with
      far = the ring iova, which we can read from the host side
In case (b) CB_FSR/FAR go non zero and the whole hypothesis set changes.
"""
import io, sys

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
MARK = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-379: the fetch question: does the device read the rings at all, and
	 * does the smmu refuse the read.  Everything here is read only apart from the
	 * two doorbells we have rung a hundred times already. */
	if (pcie_socreset == 2u && smmu_state == 1 && pcie_dma_extra != 0) {
		uint32_t i79, g79, c79, rp79, wp79, ch79, t79, moved79 = 0;
		uint32_t g0_79 = rd(smmu_mmio + 0x48);
		uint32_t f0_79 = (smmu_cb != 0) ? rd(smmu_cb + 0x58) : 0xffffffffu;
		printf("apply-379 smmu mmio 0x%llx cb 0x%llx gfsr 0x%08x cbfsr 0x%08x ee 0x%08x mh 0x%08x\n",
		    (unsigned long long)smmu_mmio, (unsigned long long)smmu_cb, g0_79, f0_79,
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48));
		for (i79 = 0; i79 < 8u; i79++) {
			printf("apply-379 er0[%u] %08x %08x %08x %08x\n", i79,
			    rd(pcie_dma_extra + 0x4000u + i79 * 16u),
			    rd(pcie_dma_extra + 0x4000u + i79 * 16u + 4u),
			    rd(pcie_dma_extra + 0x4000u + i79 * 16u + 8u),
			    rd(pcie_dma_extra + 0x4000u + i79 * 16u + 12u));
		}
		for (i79 = 0; i79 < 4u; i79++) {
			printf("apply-379 er1[%u] %08x %08x %08x %08x\n", i79,
			    rd(pcie_dma_extra + 0x5000u + i79 * 16u),
			    rd(pcie_dma_extra + 0x5000u + i79 * 16u + 4u),
			    rd(pcie_dma_extra + 0x5000u + i79 * 16u + 8u),
			    rd(pcie_dma_extra + 0x5000u + i79 * 16u + 12u));
		}
		rp79 = rd(pcie_dma_extra + 0x241cu);
		wp79 = rd(pcie_dma_extra + 0x2424u);
		printf("apply-379 cmd before: rp 0x%08x wp 0x%08x ring %08x %08x %08x %08x\n",
		    rp79, wp79, rd(pcie_dma_extra + 0x7000u), rd(pcie_dma_extra + 0x7004u),
		    rd(pcie_dma_extra + 0x7008u), rd(pcie_dma_extra + 0x700cu));
		wr(bar0.base + 0x70, wp79);
		for (t79 = 0; t79 < 100u; t79++) {
			uint32_t g = rd(smmu_mmio + 0x48);
			uint32_t f = (smmu_cb != 0) ? rd(smmu_cb + 0x58) : 0;
			if (rd(pcie_dma_extra + 0x241cu) != rp79) {
				moved79 = 1;
				printf("apply-379 cmd rp moved to 0x%08x at %u ms\n", rd(pcie_dma_extra + 0x241cu), t79);
				break;
			}
			if (g != g0_79 || f != f0_79) {
				printf("apply-379 smmu change at %u ms: gfsr 0x%08x cbfsr 0x%08x far 0x%08x%08x fsynr0 0x%08x\n",
				    t79, g, f, rd(smmu_cb + 0x64u), rd(smmu_cb + 0x60u), rd(smmu_cb + 0x68u));
			}
			sleep_ms(1);
		}
		printf("apply-379 cmd after %u ms: moved %u rp 0x%08x gfsr 0x%08x cbfsr 0x%08x far 0x%08x%08x\n",
		    t79, moved79, rd(pcie_dma_extra + 0x241cu), rd(smmu_mmio + 0x48),
		    (smmu_cb != 0) ? rd(smmu_cb + 0x58) : 0,
		    (smmu_cb != 0) ? rd(smmu_cb + 0x64u) : 0, (smmu_cb != 0) ? rd(smmu_cb + 0x60u) : 0);
		ch79 = 20u * 0x2cu;
		rp79 = rd(pcie_dma_extra + ch79 + 0x1cu);
		wp79 = rd(pcie_dma_extra + ch79 + 0x24u);
		printf("apply-379 ch20 before: st 0x%08x rp 0x%08x wp 0x%08x ring %08x %08x %08x %08x\n",
		    rd(pcie_dma_extra + ch79), rp79, wp79,
		    rd(pcie_dma_extra + 0xc000u), rd(pcie_dma_extra + 0xc004u),
		    rd(pcie_dma_extra + 0xc008u), rd(pcie_dma_extra + 0xc00cu));
		wr(bar0.base + 0x300 + 20u * 8u + 4u, 0u);
		wr(bar0.base + 0x300 + 20u * 8u, wp79);
		for (t79 = 0; t79 < 100u; t79++) {
			uint32_t g = rd(smmu_mmio + 0x48);
			uint32_t f = (smmu_cb != 0) ? rd(smmu_cb + 0x58) : 0;
			if (rd(pcie_dma_extra + ch79 + 0x1cu) != rp79 || rd(pcie_dma_extra + ch79) != 1u) {
				printf("apply-379 ch20 change at %u ms: st 0x%08x rp 0x%08x wp 0x%08x\n", t79,
				    rd(pcie_dma_extra + ch79), rd(pcie_dma_extra + ch79 + 0x1cu),
				    rd(pcie_dma_extra + ch79 + 0x24u));
				break;
			}
			if (g != g0_79 || f != f0_79) {
				printf("apply-379 smmu change at %u ms (ch): gfsr 0x%08x cbfsr 0x%08x far 0x%08x%08x\n",
				    t79, g, f, (smmu_cb != 0) ? rd(smmu_cb + 0x64u) : 0,
				    (smmu_cb != 0) ? rd(smmu_cb + 0x60u) : 0);
			}
			sleep_ms(1);
		}
		printf("apply-379 end: ee 0x%08x mh 0x%08x ch20 st 0x%08x rp 0x%08x gfsr 0x%08x cbfsr 0x%08x far 0x%08x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48),
		    rd(pcie_dma_extra + ch79), rd(pcie_dma_extra + ch79 + 0x1cu),
		    rd(smmu_mmio + 0x48), (smmu_cb != 0) ? rd(smmu_cb + 0x58) : 0,
		    (smmu_cb != 0) ? rd(smmu_cb + 0x64u) : 0, (smmu_cb != 0) ? rd(smmu_cb + 0x60u) : 0);
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(MARK) == 1, "the apply-169 marker is not unique: %d" % src.count(MARK)
assert "apply-379" not in src, "apply-379 is already in the source"
src = src.replace(MARK, BLOCK + MARK)
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-379 ok")
