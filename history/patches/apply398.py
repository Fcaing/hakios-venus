#!/usr/bin/env python3
"""apply-398: plan B -- give the endpoint a working MSI and see if that changes anything.

Every round so far armed MSI with a single vector (MME=0).  The MHI block has two event
rings, and a device that tries to signal vector 1 while only vector 0 is enabled gets its
message dropped by the root complex.  So: enable every vector the capability advertises,
clear BHI_INTVEC like the vendor does, then use the one test that has a positive control
(put a TRE with a payload pointer outside the MHI window on ch20; ch0 going to ERROR proved
the engine does fetch and fault).  If ch20 goes to ERROR too, MSI was the missing piece.
"""
import io, re

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-398: plan B.  Enable every MSI vector, clear BHI_INTVEC, then poke ch20. */
	if (pcie_mhi_data == 21u && smmu_state == 1 && pcie_dma_extra != 0 &&
	    rd(bar0.base + 0x128) == 2u) {
		uint32_t cap398 = rd(conf.base + 0x50);
		uint32_t doff398 = (cap398 & 0x80u) ? 0x5cu : 0x58u;
		uint32_t mmc398 = (cap398 >> 1) & 7u;
		uint32_t mme398 = mmc398;		/* enable everything the cap allows */
		vm_offset_t mv398 = pcie_dma_vec;
		uint32_t k398, st398, off398, wp398, rbase398;
		vm_offset_t tre398;

		printf("apply-398 a: msi cap 0x%08x mmc %u (%u vectors) 64bit %u\n",
		    cap398, mmc398, 1u << mmc398, (cap398 & 0x80u) ? 1u : 0u);
		if (mv398 != 0) {
			for (k398 = 0; k398 < 4096u; k398 += 4u)
				wr(mv398 + k398, 0xa5a5a5a5u);
			for (k398 = 0; k398 < 4096u; k398 += 64u)
				__asm__ __volatile__("dc civac, %0" :: "r"(mv398 + (vm_offset_t)k398) : "memory");
			__asm__ __volatile__("dsb sy" ::: "memory");
			wr(conf.base + 0x50, 0u);			/* off while programming */
			wr(conf.base + doff398, 0x00001000u);		/* data */
			wr(conf.base + 0x54, (uint32_t)PCIE_SMMU_VEC_IOVA);
			if (cap398 & 0x80u)
				wr(conf.base + 0x58, 0u);
			wr(conf.base + 0x50, (cap398 & 0xffff0000u) | (mme398 << 4) | 1u);
			printf("apply-398 b: armed cap 0x%08x addr 0x%08x data 0x%08x\n",
			    rd(conf.base + 0x50), rd(conf.base + 0x54), rd(conf.base + doff398));
		} else {
			printf("apply-398 b: no vector page mapped\n");
		}
		printf("apply-398 c: bhi intvec was 0x%08x\n", rd(bar0.base + 0x224 + 0x20u));
		wr(bar0.base + 0x224 + 0x20u, 0u);

		st398 = rd(pcie_dma_extra + 20u * 0x2cu);
		rbase398 = rd(pcie_dma_extra + 20u * 0x2cu + 0x0cu);
		wp398 = rd(pcie_dma_extra + 20u * 0x2cu + 0x24u);
		printf("apply-398 d: ch20 st 0x%08x rbase 0x%08x len 0x%08x rp 0x%08x wp 0x%08x\n",
		    st398, rbase398, rd(pcie_dma_extra + 20u * 0x2cu + 0x14u),
		    rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu), wp398);
		if (wp398 >= PCIE_EXTRA_IOVA && wp398 < PCIE_EXTRA_IOVA + PCIE_EXTRA_SIZE) {
			off398 = wp398 - (uint32_t)PCIE_EXTRA_IOVA;
			tre398 = pcie_dma_extra + off398;
			wr(tre398 + 0x00u, 0x80000000u);	/* outside the mhi window */
			wr(tre398 + 0x04u, 0u);
			wr(tre398 + 0x08u, 0x00000010u);
			wr(tre398 + 0x0cu, 0x00020200u);
			__asm__ __volatile__("dc civac, %0" :: "r"(tre398) : "memory");
			__asm__ __volatile__("dsb sy" ::: "memory");
			wr(pcie_dma_extra + 20u * 0x2cu + 0x24u, wp398 + 0x10u);
			wr(bar0.base + 0x300u + 20u * 8u + 4u, 0u);
			wr(bar0.base + 0x300u + 20u * 8u, wp398 + 0x10u);
			printf("apply-398 e: bad tre at 0x%llx, rang 0x3a0 with 0x%08x\n",
			    (unsigned long long)tre398, wp398 + 0x10u);
		} else {
			printf("apply-398 e: wp 0x%08x is not in the extra window\n", wp398);
		}
		for (k398 = 0; k398 < 60u; k398++) {
			sleep_ms(5);
			if ((rd(pcie_dma_extra + 20u * 0x2cu) & 0xffu) != (st398 & 0xffu)) {
				printf("apply-398 f: t=%u ms ch20 st 0x%08x\n", k398 * 5u,
				    rd(pcie_dma_extra + 20u * 0x2cu));
				break;
			}
		}
		printf("apply-398 g: end ch20 st 0x%08x ee 0x%08x mh 0x%08x er1 rp 0x%08x wp 0x%08x\n",
		    rd(pcie_dma_extra + 20u * 0x2cu), rd(bar0.base + 0x128), rd(bar0.base + 0x48),
		    rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x1cu), rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x24u));
		if (mv398 != 0)
			printf("apply-398 h: msi page %08x %08x %08x %08x | %08x %08x %08x %08x\n",
			    rd(mv398 + 0x0u), rd(mv398 + 0x4u), rd(mv398 + 0x8u), rd(mv398 + 0xcu),
			    rd(mv398 + 0x10u), rd(mv398 + 0x14u), rd(mv398 + 0x18u), rd(mv398 + 0x1cu));
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1, "end marker"
assert "apply-398" not in src

g1 = "pcie_mhi_data != 17u && pcie_chanstart != 0"
g2 = "pcie_mhi_data != 17u) wr(pcie_dma_extra + 20 * 0x2c"
assert src.count(g1) == 1, "gate 1 (apply-308) count=%d" % src.count(g1)
assert src.count(g2) == 1, "gate 2 (apply-360) count=%d" % src.count(g2)
src = src.replace(g1, "pcie_mhi_data != 17u && pcie_mhi_data != 21u && pcie_chanstart != 0")
src = src.replace(g2, "pcie_mhi_data != 17u && pcie_mhi_data != 21u) wr(pcie_dma_extra + 20 * 0x2c")

a = src.index(END)
src = src[:a] + BLOCK + src[a:]
assert src.count("apply-398 h") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-398 ok")
