#!/usr/bin/env python3
"""apply-403: the stock stack does not sit in M0, it sits in M2.

Read from the working phone through /sys/kernel/debug/mhi/1103_00:01.00:
  MHI_CNTRL 0x400, MHI_STATUS 0x401  -> mhistate 4 = M2, plus READY
  states: pm_state:M2 dev_state:M2 EE:AMSS  (M0:39 M2:38 - it is essentially never in M0)
  chan:   IPCR(20) state 0x3 (suspended) brstmode 0 type 1 erindex 1 len 0x200, wp base+0x80
          IPCR(21) state 0x3 brstmode 0 type 2 erindex 1 len 0x200, wp base+0x1e0
          LOOPBACK(0/1) state 0 base 0 len 0 - not configured at all on the real stack.
So walk the device like cnss2 does: ask for M2, then wake it with the device wake
doorbell, and only then ring the channel doorbell.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-403: m2 first, then the device wake doorbell, then the channel doorbell. */
	if (pcie_mhi_data == 24u && smmu_state == 1 && pcie_dma_extra != 0 &&
	    rd(bar0.base + 0x128) == 2u) {
		uint32_t k403, st403, wp403, off403, mh403;
		vm_offset_t tre403;

		printf("apply-403 a: mh 0x%08x ctrl 0x%08x ch20 st 0x%08x ch21 st 0x%08x\n",
		    rd(bar0.base + 0x48), rd(bar0.base + 0x38),
		    rd(pcie_dma_extra + 20u * 0x2cu), rd(pcie_dma_extra + 21u * 0x2cu));
		wr(bar0.base + 0x38, 0x00000400u);		/* mhistate 4 = m2 */
		for (k403 = 0; k403 < 40u; k403++) {
			sleep_ms(5);
			if ((rd(bar0.base + 0x48) & 0xff00u) != 0x0200u)
				break;
		}
		printf("apply-403 b: t=%u ms mh 0x%08x ctrl 0x%08x ee 0x%08x ch20 st 0x%08x\n",
		    k403 * 5u, rd(bar0.base + 0x48), rd(bar0.base + 0x38),
		    rd(bar0.base + 0x128), rd(pcie_dma_extra + 20u * 0x2cu));
		/* the device wake doorbell: CHDBOFF + 8 * MHI_DEV_WAKE_DB(127) = 0x6f8 */
		wr(bar0.base + 0x300u + 8u * 127u + 4u, 0u);
		wr(bar0.base + 0x300u + 8u * 127u, 1u);
		for (k403 = 0; k403 < 40u; k403++) {
			sleep_ms(5);
			mh403 = rd(bar0.base + 0x48);
			if ((mh403 & 0xff00u) != 0x0400u) {
				printf("apply-403 c: woke at t=%u ms mh 0x%08x ee 0x%08x\n",
				    k403 * 5u, mh403, rd(bar0.base + 0x128));
				break;
			}
		}
		mh403 = rd(bar0.base + 0x48);
		printf("apply-403 d: after wake mh 0x%08x ee 0x%08x ch20 st 0x%08x\n",
		    mh403, rd(bar0.base + 0x128), rd(pcie_dma_extra + 20u * 0x2cu));
		st403 = rd(pcie_dma_extra + 20u * 0x2cu);
		wp403 = rd(pcie_dma_extra + 20u * 0x2cu + 0x24u);
		if (wp403 >= PCIE_EXTRA_IOVA && wp403 < PCIE_EXTRA_IOVA + PCIE_EXTRA_SIZE) {
			off403 = wp403 - (uint32_t)PCIE_EXTRA_IOVA;
			tre403 = pcie_dma_extra + off403;
			wr(tre403 + 0x00u, 0x80000000u);
			wr(tre403 + 0x04u, 0u);
			wr(tre403 + 0x08u, 0x00000010u);
			wr(tre403 + 0x0cu, 0x00020200u);
			__asm__ __volatile__("dc civac, %0" :: "r"(tre403) : "memory");
			__asm__ __volatile__("dsb sy" ::: "memory");
			wr(pcie_dma_extra + 20u * 0x2cu + 0x24u, wp403 + 0x10u);
			wr(bar0.base + 0x300u + 20u * 8u + 4u, 0u);
			wr(bar0.base + 0x300u + 20u * 8u, wp403 + 0x10u);
			printf("apply-403 e: bad tre, rang 0x3a0 with 0x%08x\n", wp403 + 0x10u);
		}
		for (k403 = 0; k403 < 60u; k403++) {
			sleep_ms(5);
			if ((rd(pcie_dma_extra + 20u * 0x2cu) & 0xffu) != (st403 & 0xffu)) {
				printf("apply-403 f: t=%u ms ch20 st 0x%08x\n", k403 * 5u,
				    rd(pcie_dma_extra + 20u * 0x2cu));
				break;
			}
		}
		printf("apply-403 g: end mh 0x%08x ee 0x%08x ch20 st 0x%08x ch21 st 0x%08x er1 rp 0x%08x\n",
		    rd(bar0.base + 0x48), rd(bar0.base + 0x128),
		    rd(pcie_dma_extra + 20u * 0x2cu), rd(pcie_dma_extra + 21u * 0x2cu),
		    rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x1cu));
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1, "end marker"
assert "apply-403" not in src

a1 = "pcie_mhi_data != 22u && pcie_chanstart != 0"
a2 = "pcie_mhi_data != 22u) wr(pcie_dma_extra + 20 * 0x2c"
assert src.count(a1) == 1 and src.count(a2) == 1, "gates"
src = src.replace(a1, "pcie_mhi_data != 22u && pcie_mhi_data != 24u && pcie_chanstart != 0")
src = src.replace(a2, "pcie_mhi_data != 22u && pcie_mhi_data != 24u) wr(pcie_dma_extra + 20 * 0x2c")

a = src.index(END)
src = src[:a] + BLOCK + src[a:]
assert src.count("apply-403 g") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-403 ok")
