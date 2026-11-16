#!/usr/bin/env python3
"""apply-380: is the command ring really being read, this round.

p420 showed four CMD_COMPLETION events in the event ring, all pointing at our
four command TREs with code 1.  They could be leftovers from an earlier boot.
So: wipe the whole event ring, send exactly one start command for channel 20,
ring CRDB, and see whether a completion shows up afterwards.  A completion with
ptr = 0xa0207000 can only have been posted in response to what we just did.

Also fixes the apply-378 gate (it was "!= 0", so every later value re-ran it).
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
MARK = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-380: wipe the event ring, then send exactly one start command for
	 * channel 20 and see whether the device answers it now. */
	if (pcie_socreset == 3u && smmu_state == 1 && pcie_dma_extra != 0) {
		uint32_t i80, t80, seen80 = 0;
		uint64_t cb80 = PCIE_EXTRA_IOVA + 0x7000u, cw80 = cb80 + 16u;
		printf("apply-380 before: ee 0x%08x cmd rp 0x%08x wp 0x%08x er rp 0x%08x wp 0x%08x\n",
		    rd(bar0.base + 0x128), rd(pcie_dma_extra + 0x241cu), rd(pcie_dma_extra + 0x2424u),
		    rd(pcie_dma_extra + 0x201cu), rd(pcie_dma_extra + 0x2024u));
		for (i80 = 0; i80 < 16u; i80++) {
			wr(pcie_dma_extra + 0x4000u + i80 * 16u + 0u, 0u);
			wr(pcie_dma_extra + 0x4000u + i80 * 16u + 4u, 0u);
			wr(pcie_dma_extra + 0x4000u + i80 * 16u + 8u, 0u);
			wr(pcie_dma_extra + 0x4000u + i80 * 16u + 12u, 0u);
		}
		for (i80 = 0; i80 < 0x100u; i80 += 64) {
			__asm__ volatile("dc civac, %0" :: "r"(pcie_dma_extra + 0x4000 + i80) : "memory");
		}
		wr(pcie_dma_extra + 0x7000u, 0u);
		wr(pcie_dma_extra + 0x7004u, 0u);
		wr(pcie_dma_extra + 0x7008u, 0u);
		wr(pcie_dma_extra + 0x700cu, (20u << 24) | (0x12u << 16));
		for (i80 = 0; i80 < 0x100u; i80 += 64) {
			__asm__ volatile("dc civac, %0" :: "r"(pcie_dma_extra + 0x7000 + i80) : "memory");
		}
		wr(pcie_dma_extra + 0x2400u + 0x1cu, (uint32_t)cb80);
		wr(pcie_dma_extra + 0x2400u + 0x24u, (uint32_t)cw80);
		wr(pcie_dma_extra + 0x2400u + 0x28u, 0u);
		__asm__ volatile("dsb sy" ::: "memory");
		printf("apply-380 wiped: tre %08x %08x %08x %08x ctxt rp 0x%08x wp 0x%08x\n",
		    rd(pcie_dma_extra + 0x7000u), rd(pcie_dma_extra + 0x7004u),
		    rd(pcie_dma_extra + 0x7008u), rd(pcie_dma_extra + 0x700cu),
		    rd(pcie_dma_extra + 0x241cu), rd(pcie_dma_extra + 0x2424u));
		wr(bar0.base + 0x70, (uint32_t)cw80);
		for (t80 = 0; t80 < 200u; t80++) {
			sleep_ms(1);
			if (rd(pcie_dma_extra + 0x4000u) != 0u || rd(pcie_dma_extra + 0x4040u) != 0u ||
			    rd(pcie_dma_extra + 0x4080u) != 0u) {
				seen80 = 1;
				break;
			}
		}
		printf("apply-380 after %u ms: seen %u\n", t80, seen80);
		for (i80 = 0; i80 < 12u; i80++) {
			printf("apply-380 er[%u] %08x %08x %08x %08x\n", i80,
			    rd(pcie_dma_extra + 0x4000u + i80 * 16u),
			    rd(pcie_dma_extra + 0x4000u + i80 * 16u + 4u),
			    rd(pcie_dma_extra + 0x4000u + i80 * 16u + 8u),
			    rd(pcie_dma_extra + 0x4000u + i80 * 16u + 12u));
		}
		printf("apply-380 end: ee 0x%08x mh 0x%08x cmd rp 0x%08x ch20 st 0x%08x rp 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(pcie_dma_extra + 0x241cu),
		    rd(pcie_dma_extra + 20u * 0x2cu), rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu));
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()

old_gate = "if (pcie_socreset != 0 && smmu_state == 1) {"
new_gate = "if (pcie_socreset == 1 && smmu_state == 1) {"
assert src.count(old_gate) == 1, "apply-378 gate not found once: %d" % src.count(old_gate)
src = src.replace(old_gate, new_gate)

assert src.count(MARK) == 1, "the apply-169 marker is not unique"
assert "apply-380" not in src, "apply-380 is already in the source"
src = src.replace(MARK, BLOCK + MARK)

io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-380 ok")
