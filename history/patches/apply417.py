#!/usr/bin/env python3
"""apply-417: make every channel idle, then ask for M2.

p459 put only ch20/ch21 to ENABLED and the device still refused M2, but ch0/ch1/ch4/ch5
were left in whatever state the firmware put them (RUNNING).  `mhi_pm_m2_transition` in the
vendor only moves when *every* channel is idle, and the real device sits in M2 with all six
channels at state 3 (SUSPENDED).  So: set all six to ENABLED (0x201), ask for M2, and see
whether MHISTATUS finally changes to 0x401.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-417: all six channels idle, then M2. */
	if (pcie_mhi_data == 37u && smmu_state == 1 && pcie_dma_extra != 0 &&
	    rd(bar0.base + 0x128) == 2u) {
		uint32_t chs417[6];
		uint32_t i417, mh0 = rd(bar0.base + 0x48);

		chs417[0] = 0u; chs417[1] = 1u; chs417[2] = 4u;
		chs417[3] = 5u; chs417[4] = 20u; chs417[5] = 21u;

		printf("apply-417 a: before mh 0x%08x ctrl 0x%08x ee 0x%08x\n",
		    mh0, rd(bar0.base + 0x38), rd(bar0.base + 0x128));
		for (i417 = 0; i417 < 6u; i417++) {
			uint32_t off = chs417[i417] * 0x2cu;
			printf("apply-417 b: ch%u st 0x%08x rp 0x%08x wp 0x%08x\n", chs417[i417],
			    rd(pcie_dma_extra + off), rd(pcie_dma_extra + off + 0x1cu),
			    rd(pcie_dma_extra + off + 0x24u));
			wr(pcie_dma_extra + off, 0x00000201u);
		}
		__asm__ __volatile__("dsb sy" ::: "memory");
		sleep_ms(5);
		for (i417 = 0; i417 < 6u; i417++) {
			uint32_t off = chs417[i417] * 0x2cu;
			printf("apply-417 c: ch%u now st 0x%08x\n", chs417[i417], rd(pcie_dma_extra + off));
		}
		wr(bar0.base + 0x38, (rd(bar0.base + 0x38) & ~0xff00u) | (4u << 8));
		printf("apply-417 d: asked for m2, ctrl 0x%08x\n", rd(bar0.base + 0x38));
		for (i417 = 0; i417 < 100u; i417++) {
			sleep_ms(5);
			if ((rd(bar0.base + 0x48) & 0xff00u) != (mh0 & 0xff00u)) {
				printf("apply-417 e: t=%u ms mh 0x%08x ee 0x%08x\n", i417 * 5u + 5u,
				    rd(bar0.base + 0x48), rd(bar0.base + 0x128));
				break;
			}
		}
		printf("apply-417 f: end mh 0x%08x ctrl 0x%08x ee 0x%08x\n",
		    rd(bar0.base + 0x48), rd(bar0.base + 0x38), rd(bar0.base + 0x128));

		/* if M2 was taken, the ipcr ring must become visible to the firmware: try the bell */
		if ((rd(bar0.base + 0x48) & 0xff00u) == 0x0400u) {
			uint32_t off = 20u * 0x2cu, cwp = rd(pcie_dma_extra + off + 0x24u);
			if (cwp >= PCIE_EXTRA_IOVA && cwp < PCIE_EXTRA_IOVA + PCIE_EXTRA_SIZE) {
				vm_offset_t t = pcie_dma_extra + (cwp - (uint32_t)PCIE_EXTRA_IOVA);
				wr(t + 0x00u, 0x80000000u);
				wr(t + 0x04u, 0u);
				wr(t + 0x08u, 0x00000010u);
				wr(t + 0x0cu, 0x00020200u);
				__asm__ __volatile__("dc civac, %0" :: "r"(t) : "memory");
				__asm__ __volatile__("dsb sy" ::: "memory");
				wr(pcie_dma_extra + off + 0x24u, cwp + 0x10u);
				wr(bar0.base + 0x300u + 20u * 8u + 4u, 0u);
				wr(bar0.base + 0x300u + 20u * 8u, cwp + 0x10u);
				printf("apply-417 g: in m2, bad tre rung 0x3a0 <- 0x%08x\n", cwp + 0x10u);
			}
			sleep_ms(300);
			printf("apply-417 h: in m2 after bell ch20 0x%08x ee 0x%08x mh 0x%08x\n",
			    rd(pcie_dma_extra + 20u * 0x2cu), rd(bar0.base + 0x128), rd(bar0.base + 0x48));
		}
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1
assert "apply-417" not in src

a = "pcie_mhi_data != 36u && pcie_chanstart != 0"
assert src.count(a) == 1
src = src.replace(a, "pcie_mhi_data != 36u && pcie_mhi_data != 37u && pcie_chanstart != 0")
b = "pcie_mhi_data != 36u) wr(pcie_dma_extra + 20 * 0x2c"
assert src.count(b) == 1
src = src.replace(b, "pcie_mhi_data != 36u && pcie_mhi_data != 37u) wr(pcie_dma_extra + 20 * 0x2c")

i = src.index(END)
src = src[:i] + BLOCK + src[i:]
assert src.count("apply-417 h:") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-417 ok")
