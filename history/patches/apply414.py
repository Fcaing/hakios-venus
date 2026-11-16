#!/usr/bin/env python3
"""apply-414: ring the ch20 doorbell properly and then wait ten full seconds.

p457 waited ten seconds but never rang the bell; p430/p431 rang it and watched only 300 ms.
This round does both: queue one well formed TRE at the channel wp, write the wp into the
context, ring 0x3a0, then poll rp / er1 / EE for ten seconds, re-ringing every two seconds
in case the first bell was lost while the firmware was still settling.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-414: ring the bell, then be patient for ten seconds. */
	if (pcie_mhi_data == 34u && smmu_state == 1 && pcie_dma_extra != 0 &&
	    rd(bar0.base + 0x128) == 2u) {
		uint32_t i414, st414, rp414, wp414, e1rp414, e1wp414, ee414, mh414;
		uint32_t p_rp, p_wp, p_e1rp, p_e1wp, p_ee, p_mh;
		uint32_t cofs414 = 20u * 0x2cu;

		st414 = rd(pcie_dma_extra + cofs414);
		rp414 = rd(pcie_dma_extra + cofs414 + 0x1cu);
		wp414 = rd(pcie_dma_extra + cofs414 + 0x24u);
		e1rp414 = rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x1cu);
		e1wp414 = rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x24u);
		ee414 = rd(bar0.base + 0x128);
		mh414 = rd(bar0.base + 0x48);
		printf("apply-414 t0: ch20 st 0x%08x rp 0x%08x wp 0x%08x er1 rp 0x%08x wp 0x%08x"
		    " ee 0x%08x mh 0x%08x\n", st414, rp414, wp414, e1rp414, e1wp414, ee414, mh414);
		if (wp414 >= PCIE_EXTRA_IOVA && wp414 < PCIE_EXTRA_IOVA + PCIE_EXTRA_SIZE) {
			uint32_t off414 = wp414 - (uint32_t)PCIE_EXTRA_IOVA;
			vm_offset_t tre414 = pcie_dma_extra + off414;
			uint64_t pay414 = PCIE_EXTRA_IOVA + 0x3a0000ull;

			wr(tre414 + 0x00u, (uint32_t)pay414);
			wr(tre414 + 0x04u, (uint32_t)(pay414 >> 32));
			wr(tre414 + 0x08u, 0x00000010u);
			wr(tre414 + 0x0cu, 0x00020200u);
			__asm__ __volatile__("dc civac, %0" :: "r"(tre414) : "memory");
			__asm__ __volatile__("dsb sy" ::: "memory");
			wr(pcie_dma_extra + cofs414 + 0x24u, wp414 + 0x10u);
			wr(bar0.base + 0x3a0u + 4u, 0u);
			wr(bar0.base + 0x3a0u, wp414 + 0x10u);
			printf("apply-414 a: queued 0x%08x 0x%08x 0x10 0x00020200 at 0x%llx, rung 0x3a0 <- 0x%08x\n",
			    rd(tre414), rd(tre414 + 4u), (unsigned long long)tre414, wp414 + 0x10u);
		} else {
			printf("apply-414 a: wp 0x%08x is outside the extra window\n", wp414);
		}
		p_rp = rp414; p_wp = wp414 + 0x10u; p_e1rp = e1rp414; p_e1wp = e1wp414;
		p_ee = ee414; p_mh = mh414;
		for (i414 = 0; i414 < 100u; i414++) {
			sleep_ms(100);
			if ((i414 % 20u) == 19u) {
				wr(bar0.base + 0x3a0u + 4u, 0u);
				wr(bar0.base + 0x3a0u, rd(pcie_dma_extra + cofs414 + 0x24u));
			}
			rp414 = rd(pcie_dma_extra + cofs414 + 0x1cu);
			wp414 = rd(pcie_dma_extra + cofs414 + 0x24u);
			e1rp414 = rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x1cu);
			e1wp414 = rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x24u);
			ee414 = rd(bar0.base + 0x128);
			mh414 = rd(bar0.base + 0x48);
			if (rp414 != p_rp || wp414 != p_wp || e1rp414 != p_e1rp ||
			    e1wp414 != p_e1wp || ee414 != p_ee || mh414 != p_mh) {
				printf("apply-414 t=%u ms: ch20 st 0x%08x rp 0x%08x wp 0x%08x"
				    " er1 rp 0x%08x wp 0x%08x ee 0x%08x mh 0x%08x\n",
				    i414 * 100u + 100u, rd(pcie_dma_extra + cofs414), rp414, wp414,
				    e1rp414, e1wp414, ee414, mh414);
				p_rp = rp414; p_wp = wp414; p_e1rp = e1rp414; p_e1wp = e1wp414;
				p_ee = ee414; p_mh = mh414;
			}
		}
		/* part two: put both channels back to ENABLED (idle) and ask for M2, the state the
		 * real device sits in.  mhi_pm_m2_transition only moves when every channel is
		 * idle, so a device that refuses M2 while they are RUNNING will take it here. */
		wr(pcie_dma_extra + 20u * 0x2cu, 0x00000201u);
		wr(pcie_dma_extra + 21u * 0x2cu, 0x00000201u);
		__asm__ __volatile__("dsb sy" ::: "memory");
		printf("apply-414 b: channels set to 0x201, asking for m2 (ctrl 0x%08x -> 0x400)\n",
		    rd(bar0.base + 0x38));
		wr(bar0.base + 0x38, (rd(bar0.base + 0x38) & ~0xff00u) | (4u << 8));
		for (i414 = 0; i414 < 40u; i414++) {
			sleep_ms(10);
			if ((rd(bar0.base + 0x48) & 0xff00u) != (mh414 & 0xff00u)) {
				printf("apply-414 c: t=%u ms mh 0x%08x ee 0x%08x\n", i414 * 10u + 10u,
				    rd(bar0.base + 0x48), rd(bar0.base + 0x128));
				break;
			}
		}
		printf("apply-414 end: ch20 st 0x%08x rp 0x%08x wp 0x%08x er1 rp 0x%08x wp 0x%08x ee 0x%08x\n",
		    rd(pcie_dma_extra + cofs414), rd(pcie_dma_extra + cofs414 + 0x1cu),
		    rd(pcie_dma_extra + cofs414 + 0x24u),
		    rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x1cu),
		    rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x24u), rd(bar0.base + 0x128));
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1
assert "apply-414" not in src

a = "pcie_mhi_data != 33u && pcie_chanstart != 0"
assert src.count(a) == 1
src = src.replace(a, "pcie_mhi_data != 33u && pcie_mhi_data != 34u && pcie_chanstart != 0")
b = "pcie_mhi_data != 33u) wr(pcie_dma_extra + 20 * 0x2c"
assert src.count(b) == 1
src = src.replace(b, "pcie_mhi_data != 33u && pcie_mhi_data != 34u) wr(pcie_dma_extra + 20 * 0x2c")

i = src.index(END)
src = src[:i] + BLOCK + src[i:]
assert src.count("apply-414 end:") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-414 ok")
