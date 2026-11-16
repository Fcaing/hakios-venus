#!/usr/bin/env python3
"""apply-421: the clean host-side open: ENABLED, START, then a TRE.

apply-420 proved the command ring answers START_CHAN(20) with CMD_COMPLETION code 1, while the
channel's data ring is still never fetched.  One order has not been tried in steady state:
put ch20 back to ENABLED (0x201) with an empty ring, then let START move it to RUNNING, then
push a TRE.  If the firmware's consumer only arms on a host-initiated open, this is where the
ring would finally move.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-421: ENABLED -> START_CHAN(20) -> TRE, all in steady state. */
	if (pcie_mhi_data == 41u && smmu_state == 1 && pcie_dma_extra != 0 &&
	    rd(bar0.base + 0x128) == 2u) {
		uint32_t i421, cwp421, wp421;
		vm_offset_t t421;

		for (i421 = 0; i421 < 20u; i421++)
			sleep_ms(100);
		printf("apply-421 a: settled ch20 0x%08x rbase 0x%08x rlen 0x%08x rp 0x%08x wp 0x%08x ee 0x%08x mh 0x%08x\n",
		    rd(pcie_dma_extra + 20u * 0x2cu), rd(pcie_dma_extra + 20u * 0x2cu + 0x0cu),
		    rd(pcie_dma_extra + 20u * 0x2cu + 0x14u), rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu),
		    rd(pcie_dma_extra + 20u * 0x2cu + 0x24u), rd(bar0.base + 0x128), rd(bar0.base + 0x48));

		/* 1: ENABLED, empty ring */
		wr(pcie_dma_extra + 20u * 0x2cu, 0x00000201u);
		wr(pcie_dma_extra + 20u * 0x2cu + 0x1cu, rd(pcie_dma_extra + 20u * 0x2cu + 0x0cu));
		wr(pcie_dma_extra + 20u * 0x2cu + 0x24u, rd(pcie_dma_extra + 20u * 0x2cu + 0x0cu));
		printf("apply-421 b: ch20 set to 0x201, rp=wp=rbase 0x%08x\n",
		    rd(pcie_dma_extra + 20u * 0x2cu + 0x0cu));

		/* 2: START_CHAN(20) */
		cwp421 = rd(pcie_dma_extra + 0x2400u + 0x24u);
		t421 = pcie_dma_extra + (cwp421 - (uint32_t)PCIE_EXTRA_IOVA);
		wr(t421 + 0x00u, 0u);
		wr(t421 + 0x04u, 0u);
		wr(t421 + 0x08u, 0u);
		wr(t421 + 0x0cu, 0x14120000u);
		__asm__ __volatile__("dc civac, %0" :: "r"(t421) : "memory");
		__asm__ __volatile__("dsb sy" ::: "memory");
		wr(pcie_dma_extra + 0x2400u + 0x24u, cwp421 + 0x10u);
		wr(bar0.base + 0x70u + 4u, 0u);
		wr(bar0.base + 0x70u, cwp421 + 0x10u);
		for (i421 = 0; i421 < 100u; i421++) {
			sleep_ms(3);
			if ((rd(pcie_dma_extra + 20u * 0x2cu) & 0xffu) == 0x02u)
				break;
		}
		printf("apply-421 c: %u ms after START ch20 0x%08x ee 0x%08x mh 0x%08x\n", i421 * 3u,
		    rd(pcie_dma_extra + 20u * 0x2cu), rd(bar0.base + 0x128), rd(bar0.base + 0x48));

		/* 3: a TRE at the wp the context now has */
		wp421 = rd(pcie_dma_extra + 20u * 0x2cu + 0x24u);
		if (wp421 >= PCIE_EXTRA_IOVA && wp421 < PCIE_EXTRA_IOVA + PCIE_EXTRA_SIZE) {
			t421 = pcie_dma_extra + (wp421 - (uint32_t)PCIE_EXTRA_IOVA);
			wr(t421 + 0x00u, (uint32_t)(PCIE_EXTRA_IOVA + 0x3a0000u));
			wr(t421 + 0x04u, 0u);
			wr(t421 + 0x08u, 0x00000200u);
			wr(t421 + 0x0cu, 0x00020200u);
			__asm__ __volatile__("dc civac, %0" :: "r"(t421) : "memory");
			__asm__ __volatile__("dsb sy" ::: "memory");
			wr(pcie_dma_extra + 20u * 0x2cu + 0x24u, wp421 + 0x10u);
			wr(bar0.base + 0x300u + 20u * 8u + 4u, 0u);
			wr(bar0.base + 0x300u + 20u * 8u, wp421 + 0x10u);
			printf("apply-421 d: tre at 0x%08x rung 0x3a0 <- 0x%08x\n", wp421, wp421 + 0x10u);
		} else {
			printf("apply-421 d: wp 0x%08x outside the window\n", wp421);
		}
		for (i421 = 0; i421 < 300u; i421++) {
			sleep_ms(2);
			if ((rd(pcie_dma_extra + 20u * 0x2cu) & 0xffu) != 0x02u ||
			    rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x1cu) != 0xa0205000u)
				break;
		}
		printf("apply-421 e: %u ms after tre ch20 0x%08x rp 0x%08x wp 0x%08x er1 rp 0x%08x ee 0x%08x mh 0x%08x\n",
		    i421 * 2u, rd(pcie_dma_extra + 20u * 0x2cu),
		    rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu), rd(pcie_dma_extra + 20u * 0x2cu + 0x24u),
		    rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x1cu), rd(bar0.base + 0x128), rd(bar0.base + 0x48));
		for (cwp421 = 0; cwp421 < 8u; cwp421++) {
			uint32_t o = 0x4000u + cwp421 * 16u;
			printf("apply-421 f: er0[%u] %08x %08x %08x %08x\n", cwp421,
			    rd(pcie_dma_extra + o + 0x0u), rd(pcie_dma_extra + o + 0x4u),
			    rd(pcie_dma_extra + o + 0x8u), rd(pcie_dma_extra + o + 0xcu));
		}
		for (cwp421 = 0; cwp421 < 2u; cwp421++) {
			uint32_t o = 0x5000u + cwp421 * 16u;
			printf("apply-421 g: er1[%u] %08x %08x %08x %08x\n", cwp421,
			    rd(pcie_dma_extra + o + 0x0u), rd(pcie_dma_extra + o + 0x4u),
			    rd(pcie_dma_extra + o + 0x8u), rd(pcie_dma_extra + o + 0xcu));
		}
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1
assert "apply-421" not in src

a = "pcie_mhi_data != 39u && pcie_mhi_data != 40u && pcie_chanstart != 0"
assert src.count(a) == 1
src = src.replace(a, "pcie_mhi_data != 39u && pcie_mhi_data != 40u && pcie_mhi_data != 41u && pcie_chanstart != 0")
b = "pcie_mhi_data != 39u && pcie_mhi_data != 40u) wr(pcie_dma_extra + 20 * 0x2c"
assert src.count(b) == 1
src = src.replace(b, "pcie_mhi_data != 39u && pcie_mhi_data != 40u && pcie_mhi_data != 41u) wr(pcie_dma_extra + 20 * 0x2c")

i = src.index(END)
src = src[:i] + BLOCK + src[i:]
assert src.count("apply-421 g:") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-421 ok")
