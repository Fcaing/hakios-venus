#!/usr/bin/env python3
"""apply-420: START_CHAN(20) after the settle, then immediately a TRE.

p463: a lone START_CHAN(20), two seconds after M0, came back as CMD_COMPLETION code 1.
p464: TREs on ch20 with no START are ignored.
So the missing order may be START first, TRE right after: this sends the command, waits for
its completion, then queues one TRE on the same channel and rings its doorbell.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-420: settle, START_CHAN(20), completion, then one TRE. */
	if (pcie_mhi_data == 40u && smmu_state == 1 && pcie_dma_extra != 0 &&
	    rd(bar0.base + 0x128) == 2u) {
		uint32_t i420, cwp420, off420, er0wp;
		vm_offset_t t420;

		for (i420 = 0; i420 < 20u; i420++)
			sleep_ms(100);
		printf("apply-420 a: settled ee 0x%08x mh 0x%08x ch20 0x%08x rp 0x%08x wp 0x%08x er0 rp 0x%08x wp 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(pcie_dma_extra + 20u * 0x2cu),
		    rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu), rd(pcie_dma_extra + 20u * 0x2cu + 0x24u),
		    rd(pcie_dma_extra + 0x2000u + 0x1cu), rd(pcie_dma_extra + 0x2000u + 0x24u));

		/* START_CHAN(20) */
		cwp420 = rd(pcie_dma_extra + 0x2400u + 0x24u);
		t420 = pcie_dma_extra + (cwp420 - (uint32_t)PCIE_EXTRA_IOVA);
		wr(t420 + 0x00u, 0u);
		wr(t420 + 0x04u, 0u);
		wr(t420 + 0x08u, 0u);
		wr(t420 + 0x0cu, 0x14120000u);
		__asm__ __volatile__("dc civac, %0" :: "r"(t420) : "memory");
		__asm__ __volatile__("dsb sy" ::: "memory");
		wr(pcie_dma_extra + 0x2400u + 0x24u, cwp420 + 0x10u);
		wr(bar0.base + 0x70u + 4u, 0u);
		wr(bar0.base + 0x70u, cwp420 + 0x10u);
		printf("apply-420 b: START(20) rung at 0x%08x\n", cwp420 + 0x10u);

		er0wp = rd(pcie_dma_extra + 0x2000u + 0x24u);
		for (i420 = 0; i420 < 150u; i420++) {
			sleep_ms(2);
			if (rd(pcie_dma_extra + 0x2000u + 0x24u) != er0wp)
				break;
		}
		printf("apply-420 c: %u ms after start ch20 0x%08x er0 rp 0x%08x wp 0x%08x ee 0x%08x mh 0x%08x\n",
		    i420 * 2u, rd(pcie_dma_extra + 20u * 0x2cu),
		    rd(pcie_dma_extra + 0x2000u + 0x1cu), rd(pcie_dma_extra + 0x2000u + 0x24u),
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48));

		/* the TRE, right after the command */
		cwp420 = rd(pcie_dma_extra + 20u * 0x2cu + 0x24u);
		if (cwp420 >= PCIE_EXTRA_IOVA && cwp420 < PCIE_EXTRA_IOVA + PCIE_EXTRA_SIZE) {
			t420 = pcie_dma_extra + (cwp420 - (uint32_t)PCIE_EXTRA_IOVA);
			wr(t420 + 0x00u, (uint32_t)(PCIE_EXTRA_IOVA + 0x3a0000u));
			wr(t420 + 0x04u, 0u);
			wr(t420 + 0x08u, 0x00000020u);
			wr(t420 + 0x0cu, 0x00020200u);
			__asm__ __volatile__("dc civac, %0" :: "r"(t420) : "memory");
			__asm__ __volatile__("dsb sy" ::: "memory");
			wr(pcie_dma_extra + 20u * 0x2cu + 0x24u, cwp420 + 0x10u);
			wr(bar0.base + 0x300u + 20u * 8u + 4u, 0u);
			wr(bar0.base + 0x300u + 20u * 8u, cwp420 + 0x10u);
			printf("apply-420 d: tre at 0x%08x rung 0x3a0 <- 0x%08x\n", cwp420, cwp420 + 0x10u);
		} else {
			printf("apply-420 d: ch20 wp 0x%08x outside the window\n", cwp420);
		}
		for (i420 = 0; i420 < 400u; i420++) {
			sleep_ms(2);
			if (rd(pcie_dma_extra + 20u * 0x2cu + 0x24u) != cwp420 + 0x10u ||
			    rd(pcie_dma_extra + 0x2000u + 0x1cu) != 0xa0205000u)
				break;
		}
		printf("apply-420 e: %u ms after tre ch20 0x%08x rp 0x%08x wp 0x%08x er1 rp 0x%08x wp 0x%08x ee 0x%08x mh 0x%08x\n",
		    i420 * 2u, rd(pcie_dma_extra + 20u * 0x2cu),
		    rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu), rd(pcie_dma_extra + 20u * 0x2cu + 0x24u),
		    rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x1cu), rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x24u),
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48));
		for (off420 = 0; off420 < 10u; off420++) {
			uint32_t o = 0x4000u + off420 * 16u;
			printf("apply-420 f: er0[%u] %08x %08x %08x %08x\n", off420,
			    rd(pcie_dma_extra + o + 0x0u), rd(pcie_dma_extra + o + 0x4u),
			    rd(pcie_dma_extra + o + 0x8u), rd(pcie_dma_extra + o + 0xcu));
		}
		for (off420 = 0; off420 < 4u; off420++) {
			uint32_t o = 0x5000u + off420 * 16u;
			printf("apply-420 g: er1[%u] %08x %08x %08x %08x\n", off420,
			    rd(pcie_dma_extra + o + 0x0u), rd(pcie_dma_extra + o + 0x4u),
			    rd(pcie_dma_extra + o + 0x8u), rd(pcie_dma_extra + o + 0xcu));
		}
		printf("apply-420 h: payload %08x %08x\n",
		    rd(pcie_dma_extra + 0x3a0000u), rd(pcie_dma_extra + 0x3a0004u));
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1
assert "apply-420" not in src

a = "pcie_mhi_data != 39u && pcie_chanstart != 0"
assert src.count(a) == 1
src = src.replace(a, "pcie_mhi_data != 39u && pcie_mhi_data != 40u && pcie_chanstart != 0")
b = "pcie_mhi_data != 39u) wr(pcie_dma_extra + 20 * 0x2c"
assert src.count(b) == 1
src = src.replace(b, "pcie_mhi_data != 39u && pcie_mhi_data != 40u) wr(pcie_dma_extra + 20 * 0x2c")

i = src.index(END)
src = src[:i] + BLOCK + src[i:]
assert src.count("apply-420 h:") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-420 ok")
