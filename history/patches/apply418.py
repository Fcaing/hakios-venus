#!/usr/bin/env python3
"""apply-418: start the ipcr channel late instead of in the honeymoon.

Every round so far sent START_CHAN within milliseconds of EE becoming 2.  Early in boot the
command ring answers (four completions with code 1).  Later, the very same command asserts the
firmware.  So: wait two seconds after M0 is established, then send exactly one START_CHAN(20)
and watch the completion, EE and the channel state.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-418: START_CHAN(20) two seconds after the device reached M0. */
	if (pcie_mhi_data == 38u && smmu_state == 1 && pcie_dma_extra != 0 &&
	    rd(bar0.base + 0x128) == 2u) {
		uint32_t i418, cwp418, crb418, st418;
		vm_offset_t tre418;

		printf("apply-418 a: ee 0x%08x mh 0x%08x ch20 0x%08x ctrl 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(pcie_dma_extra + 20u * 0x2cu),
		    rd(bar0.base + 0x38));
		for (i418 = 0; i418 < 20u; i418++)
			sleep_ms(100);
		printf("apply-418 b: after 2 s ee 0x%08x mh 0x%08x ch20 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(pcie_dma_extra + 20u * 0x2cu));

		crb418 = rd(pcie_dma_extra + 0x2400u + 0x0cu);
		cwp418 = rd(pcie_dma_extra + 0x2400u + 0x24u);
		printf("apply-418 c: cmd rbase 0x%08x rp 0x%08x wp 0x%08x\n", crb418,
		    rd(pcie_dma_extra + 0x2400u + 0x1cu), cwp418);
		if (cwp418 >= PCIE_EXTRA_IOVA && cwp418 < PCIE_EXTRA_IOVA + PCIE_EXTRA_SIZE) {
			tre418 = pcie_dma_extra + (cwp418 - (uint32_t)PCIE_EXTRA_IOVA);
			wr(tre418 + 0x00u, 0u);
			wr(tre418 + 0x04u, 0u);
			wr(tre418 + 0x08u, 0u);
			wr(tre418 + 0x0cu, 0x14120000u);	/* START_CHAN(20) */
			__asm__ __volatile__("dc civac, %0" :: "r"(tre418) : "memory");
			__asm__ __volatile__("dsb sy" ::: "memory");
			wr(pcie_dma_extra + 0x2400u + 0x24u, cwp418 + 0x10u);
			wr(bar0.base + 0x70u + 4u, 0u);
			wr(bar0.base + 0x70u, cwp418 + 0x10u);
			printf("apply-418 d: start20 rung at 0x%08x\n", cwp418 + 0x10u);
		} else {
			printf("apply-418 d: cmd wp 0x%08x outside the window\n", cwp418);
		}

		st418 = rd(pcie_dma_extra + 20u * 0x2cu);
		for (i418 = 0; i418 < 300u; i418++) {
			sleep_ms(1);
			if ((rd(bar0.base + 0x48) & 0xff00u) != 0x0200u ||
			    (rd(pcie_dma_extra + 20u * 0x2cu) & 0xffu) != (st418 & 0xffu)) {
				printf("apply-418 e: t=%u ms ee 0x%08x mh 0x%08x ch20 0x%08x\n",
				    i418 + 1u, rd(bar0.base + 0x128), rd(bar0.base + 0x48),
				    rd(pcie_dma_extra + 20u * 0x2cu));
				break;
			}
		}
		printf("apply-418 f: end ee 0x%08x mh 0x%08x ch20 0x%08x cmd rp 0x%08x wp 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(pcie_dma_extra + 20u * 0x2cu),
		    rd(pcie_dma_extra + 0x2400u + 0x1cu), rd(pcie_dma_extra + 0x2400u + 0x24u));
		for (i418 = 0; i418 < 8u; i418++) {
			uint32_t off418 = 0x4000u + i418 * 16u;
			printf("apply-418 g: er0[%u] %08x %08x %08x %08x\n", i418,
			    rd(pcie_dma_extra + off418 + 0x0u), rd(pcie_dma_extra + off418 + 0x4u),
			    rd(pcie_dma_extra + off418 + 0x8u), rd(pcie_dma_extra + off418 + 0xcu));
		}
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1
assert "apply-418" not in src

a = "pcie_mhi_data != 37u && pcie_chanstart != 0"
assert src.count(a) == 1
src = src.replace(a, "pcie_mhi_data != 37u && pcie_mhi_data != 38u && pcie_chanstart != 0")
b = "pcie_mhi_data != 37u) wr(pcie_dma_extra + 20 * 0x2c"
assert src.count(b) == 1
src = src.replace(b, "pcie_mhi_data != 37u && pcie_mhi_data != 38u) wr(pcie_dma_extra + 20 * 0x2c")

i = src.index(END)
src = src[:i] + BLOCK + src[i:]
assert src.count("apply-418 g:") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-418 ok")
