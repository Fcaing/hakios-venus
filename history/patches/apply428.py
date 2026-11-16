#!/usr/bin/env python3
"""apply-428: restore MHICFG.NHWER and clear IEOT in the data TRE.

Two things the audit left untested:
  * the device comes out of reset reporting MHICFG = 0x02030880 (NHWER = 2); we rewrite it
    as 0x00030880 (NHWER = 0).  Put the device's own value back.
  * MHI_TRE_DATA_DWORD1() has bit 9 = IEOT ("interrupt on end of transfer"), which the
    vendor only sets on the last element of a ring.  We have always set it.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-428: device's own MHICFG (NHWER=2) plus a TRE with IEOT clear. */
	if (pcie_mhi_data == 48u && smmu_state == 1 && pcie_dma_extra != 0 &&
	    rd(bar0.base + 0x128) == 2u) {
		uint32_t c428, wp428, rp428, k428, cfg428;
		vm_offset_t tre428, buf428;

		sleep_ms(1500);
		c428 = 20u * 0x2cu;
		cfg428 = rd(bar0.base + 0x10);
		printf("apply-428 a: cfg before 0x%08x ch20 st 0x%08x wp 0x%08x\n",
		    cfg428, rd(pcie_dma_extra + c428), rd(pcie_dma_extra + c428 + 0x24u));
		wr(bar0.base + 0x10, (cfg428 & 0x00ffffffu) | 0x02000000u);
		printf("apply-428 b: cfg after 0x%08x (NHWER restored to 2)\n", rd(bar0.base + 0x10));

		buf428 = pcie_dma_extra + 0x3a0000u;
		for (k428 = 0; k428 < 8u; k428++)
			wr(buf428 + k428 * 4u, 0x5154524bu + k428);
		__asm__ __volatile__("dc civac, %0" :: "r"(buf428) : "memory");

		rp428 = rd(pcie_dma_extra + c428 + 0x1cu);
		wp428 = rd(pcie_dma_extra + c428 + 0x24u);
		tre428 = pcie_dma_extra + (wp428 - (uint32_t)PCIE_EXTRA_IOVA);
		wr(tre428 + 0x00u, (uint32_t)(PCIE_EXTRA_IOVA + 0x3a0000u));
		wr(tre428 + 0x04u, 0u);
		wr(tre428 + 0x08u, 0x00000020u);
		wr(tre428 + 0x0cu, 0x00020000u);	/* IEOT clear */
		__asm__ __volatile__("dc civac, %0" :: "r"(tre428) : "memory");
		__asm__ __volatile__("dsb sy" ::: "memory");
		wr(pcie_dma_extra + c428 + 0x24u, wp428 + 0x10u);
		wr(bar0.base + 0x300u + 20u * 8u + 4u, 0u);
		wr(bar0.base + 0x300u + 20u * 8u, wp428 + 0x10u);
		printf("apply-428 c: tre 0x%llx dword1 0x00020000, rung 0x3a0 <- 0x%08x\n",
		    (unsigned long long)tre428, wp428 + 0x10u);
		for (k428 = 0; k428 < 300u; k428++) {
			sleep_ms(10);
			if (rd(pcie_dma_extra + c428 + 0x1cu) != rp428 || rd(pcie_dma_extra + c428) != 0x00000202u)
				break;
		}
		printf("apply-428 d: after 3 s ch20 st 0x%08x rp 0x%08x wp 0x%08x ee 0x%08x mh 0x%08x cfg 0x%08x\n",
		    rd(pcie_dma_extra + c428), rd(pcie_dma_extra + c428 + 0x1cu), rd(pcie_dma_extra + c428 + 0x24u),
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(bar0.base + 0x10));
		printf("apply-428 e: er0 rp 0x%08x wp 0x%08x | er1 rp 0x%08x wp 0x%08x | payload %08x\n",
		    rd(pcie_dma_extra + 0x2000u + 0x1cu), rd(pcie_dma_extra + 0x2000u + 0x24u),
		    rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x1cu), rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x24u),
		    rd(buf428));
		printf("apply-428 done\n");
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1 and "apply-428" not in src

a1 = "pcie_mhi_data != 47u && pcie_chanstart != 0"
a2 = "pcie_mhi_data != 47u) wr(pcie_dma_extra + 20 * 0x2c"
assert src.count(a1) == 1, "gate A"
assert src.count(a2) == 1, "gate B"
src = src.replace(a1, "pcie_mhi_data != 47u && pcie_mhi_data != 48u && pcie_chanstart != 0")
src = src.replace(a2, "pcie_mhi_data != 47u && pcie_mhi_data != 48u) wr(pcie_dma_extra + 20 * 0x2c")

a = src.index(END)
src = src[:a] + BLOCK + src[a:]
assert src.count("apply-428 done") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-428 ok")
