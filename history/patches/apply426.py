#!/usr/bin/env python3
"""apply-426: the vendor's order - M0 first, then ring the channel doorbell.

mhi_pm_m0_transition() writes MHICTRL = M0 and *then* walks every channel and rings its
doorbell for any ring that has work queued.  Every round we have run so far rang the ch20
doorbell while MHICTRL was whatever it was (0x200 left over), never as part of an explicit
M0 transition with a TRE already queued.  This does exactly that, with the firmware's own
context untouched apart from the write pointer the host owns.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-426: queue a TRE, then ask for M0, then ring - the vendor's order. */
	if (pcie_mhi_data == 46u && smmu_state == 1 && pcie_dma_extra != 0 &&
	    rd(bar0.base + 0x128) == 2u) {
		uint32_t wp426, rp426, st426, k426, tre426off;
		vm_offset_t tre426, buf426;

		sleep_ms(1500);
		st426 = rd(pcie_dma_extra + 20u * 0x2cu);
		rp426 = rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu);
		wp426 = rd(pcie_dma_extra + 20u * 0x2cu + 0x24u);
		buf426 = pcie_dma_extra + 0x3a0000u;
		for (k426 = 0; k426 < 8u; k426++)
			wr(buf426 + k426 * 4u, 0x5154524bu + k426);
		__asm__ __volatile__("dc civac, %0" :: "r"(buf426) : "memory");
		printf("apply-426 a: settled ch20 st 0x%08x rp 0x%08x wp 0x%08x mh 0x%08x ctrl 0x%08x\n",
		    st426, rp426, wp426, rd(bar0.base + 0x48), rd(bar0.base + 0x38));
		if (wp426 >= (uint32_t)PCIE_EXTRA_IOVA && wp426 < (uint32_t)(PCIE_EXTRA_IOVA + 0x100000u)) {
			tre426off = wp426 - (uint32_t)PCIE_EXTRA_IOVA;
			tre426 = pcie_dma_extra + tre426off;
			wr(tre426 + 0x00u, (uint32_t)(PCIE_EXTRA_IOVA + 0x3a0000u));
			wr(tre426 + 0x04u, 0u);
			wr(tre426 + 0x08u, 0x00000020u);
			wr(tre426 + 0x0cu, 0x00020200u);
			__asm__ __volatile__("dc civac, %0" :: "r"(tre426) : "memory");
			__asm__ __volatile__("dsb sy" ::: "memory");
			wr(pcie_dma_extra + 20u * 0x2cu + 0x24u, wp426 + 0x10u);
			printf("apply-426 b: tre at 0x%llx, ctx wp -> 0x%08x\n",
			    (unsigned long long)tre426, wp426 + 0x10u);
			/* the vendor's mhi_pm_m0_transition: state first, doorbells after */
			wr(bar0.base + 0x38, 0x00000200u);
			printf("apply-426 c: asked for m0, mh 0x%08x ctrl 0x%08x\n",
			    rd(bar0.base + 0x48), rd(bar0.base + 0x38));
			sleep_ms(5);
			wr(bar0.base + 0x300u + 20u * 8u + 4u, 0u);
			wr(bar0.base + 0x300u + 20u * 8u, wp426 + 0x10u);
			printf("apply-426 d: rung 0x3a0 <- 0x%08x after m0\n", wp426 + 0x10u);
		} else {
			printf("apply-426 b: wp 0x%08x outside the window\n", wp426);
		}
		for (k426 = 0; k426 < 300u; k426++) {
			sleep_ms(10);
			if (rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu) != rp426 ||
			    rd(pcie_dma_extra + 20u * 0x2cu) != st426) {
				printf("apply-426 e: t=%u ms ch20 st 0x%08x rp 0x%08x wp 0x%08x ee 0x%08x\n",
				    k426 * 10u, rd(pcie_dma_extra + 20u * 0x2cu),
				    rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu), rd(pcie_dma_extra + 20u * 0x2cu + 0x24u),
				    rd(bar0.base + 0x128));
				break;
			}
			if (k426 == 100u || k426 == 200u) {
				wr(bar0.base + 0x300u + 20u * 8u + 4u, 0u);
				wr(bar0.base + 0x300u + 20u * 8u, wp426 + 0x10u);
				printf("apply-426 f: re-rung at t=%u ms\n", k426 * 10u);
			}
		}
		printf("apply-426 g: end ch20 st 0x%08x rp 0x%08x wp 0x%08x ee 0x%08x mh 0x%08x er1 rp 0x%08x wp 0x%08x\n",
		    rd(pcie_dma_extra + 20u * 0x2cu), rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu),
		    rd(pcie_dma_extra + 20u * 0x2cu + 0x24u), rd(bar0.base + 0x128), rd(bar0.base + 0x48),
		    rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x1cu), rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x24u));
		printf("apply-426 h: payload %08x %08x %08x %08x\n",
		    rd(buf426 + 0x0u), rd(buf426 + 0x4u), rd(buf426 + 0x8u), rd(buf426 + 0xcu));
		printf("apply-426 done\n");
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1, "end marker"
assert "apply-426" not in src

a1 = "pcie_mhi_data != 44u && pcie_mhi_data != 45u && pcie_chanstart != 0"
a2 = "pcie_mhi_data != 44u && pcie_mhi_data != 45u) wr(pcie_dma_extra + 20 * 0x2c"
assert src.count(a1) == 1, "gate A"
assert src.count(a2) == 1, "gate B"
src = src.replace(a1, "pcie_mhi_data != 44u && pcie_mhi_data != 45u && pcie_mhi_data != 46u && pcie_chanstart != 0")
src = src.replace(a2, "pcie_mhi_data != 44u && pcie_mhi_data != 45u && pcie_mhi_data != 46u) wr(pcie_dma_extra + 20 * 0x2c")

a = src.index(END)
src = src[:a] + BLOCK + src[a:]
assert src.count("apply-426 done") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-426 ok")
