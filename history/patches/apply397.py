#!/usr/bin/env python3
"""apply-397 (data=20): give ch20 the ring the vendor driver actually gives it - 64 elements.

Everything so far used rlen 0x200 (32 x 16-byte TREs) for ch20, because that is what the
firmware's own context said when we first read it.  ath11k's qca6390 table says num_elements 64
for the IPCR channels, i.e. rlen 0x400, and the host is the side that writes channel contexts.
If the firmware's IPCR client validates the ring length before it ever fetches, 0x200 would be
exactly the kind of thing that makes it stay quiet without any error.

Rebuild ch20's context the vendor way (chstate ENABLED, brstmode 2, chtype 1, erindex 1,
rbase 0xa020c000, rlen 0x400, rp = wp = rbase), put one TRE with a payload pointer outside the
MHI window at the head, publish wp, ring 0x3a0 and watch.  A fault => it fetched.  Silence =>
the length was not the problem either.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
START = "\t/* apply-396: "

BLOCK = r'''	/* apply-397: rebuild ch20 with a 64-element ring, then the bad-TRE detector. */
	if (pcie_mhi_data == 20u && smmu_state == 1 && pcie_dma_extra != 0) {
		uint32_t o97 = 20u * 0x2cu, w97, st97;
		uint32_t ro97 = 0xc000u;		/* ch20's ring, iova - PCIE_EXTRA_IOVA */

		printf("apply-397 before: st 0x%08x chtype 0x%08x eri 0x%08x rbase 0x%08x rlen 0x%08x rp 0x%08x wp 0x%08x\n",
		    rd(pcie_dma_extra + o97), rd(pcie_dma_extra + o97 + 0x04u), rd(pcie_dma_extra + o97 + 0x08u),
		    rd(pcie_dma_extra + o97 + 0x0cu), rd(pcie_dma_extra + o97 + 0x14u),
		    rd(pcie_dma_extra + o97 + 0x1cu), rd(pcie_dma_extra + o97 + 0x24u));
		wr(pcie_dma_extra + o97, 0x00000201u);		/* RUNNING is the device's, ENABLED + brst 2 ours */
		wr(pcie_dma_extra + o97 + 0x04u, 1u);		/* chtype: transfer */
		wr(pcie_dma_extra + o97 + 0x08u, 1u);		/* erindex 1 */
		wr(pcie_dma_extra + o97 + 0x0cu, (uint32_t)(PCIE_EXTRA_IOVA + ro97));
		wr(pcie_dma_extra + o97 + 0x10u, 0u);
		wr(pcie_dma_extra + o97 + 0x14u, 0x400u);	/* 64 elements, as ath11k configures it */
		wr(pcie_dma_extra + o97 + 0x1cu, (uint32_t)(PCIE_EXTRA_IOVA + ro97));
		wr(pcie_dma_extra + o97 + 0x24u, (uint32_t)(PCIE_EXTRA_IOVA + ro97));
		printf("apply-397 rebuilt: st 0x%08x rlen 0x%08x rp 0x%08x wp 0x%08x\n",
		    rd(pcie_dma_extra + o97), rd(pcie_dma_extra + o97 + 0x14u),
		    rd(pcie_dma_extra + o97 + 0x1cu), rd(pcie_dma_extra + o97 + 0x24u));

		/* one TRE the device cannot complete: payload 0x80000000 is outside MHICTRLBASE..LIMIT */
		wr(pcie_dma_extra + ro97, 0x80000000u);
		wr(pcie_dma_extra + ro97 + 4u, 0u);
		wr(pcie_dma_extra + ro97 + 8u, (0x1000u << 16) | 0x0200u);
		wr(pcie_dma_extra + ro97 + 12u, (20u << 24) | (2u << 16));
		wr(pcie_dma_extra + o97 + 0x24u, (uint32_t)(PCIE_EXTRA_IOVA + ro97 + 0x10u));
		wr(bar0.base + 0x6f8, 1u);
		sleep_ms(2);
		wr(bar0.base + 0x6f8, 0u);
		wr(bar0.base + 0x300 + 20u * 8u + 4u, 0u);
		wr(bar0.base + 0x300 + 20u * 8u, (uint32_t)(PCIE_EXTRA_IOVA + ro97 + 0x10u));
		for (w97 = 0; w97 < 20u; w97++) {
			sleep_ms(15);
			st97 = rd(pcie_dma_extra + o97);
			if ((st97 & 0xffu) != 0x02u || rd(bar0.base + 0x128) != 2u)
				break;
		}
		printf("apply-397 after %u ms: st 0x%08x ee 0x%08x mh 0x%08x rp 0x%08x wp 0x%08x\n",
		    (w97 + 1u) * 15u, st97, rd(bar0.base + 0x128), rd(bar0.base + 0x48),
		    rd(pcie_dma_extra + o97 + 0x1cu), rd(pcie_dma_extra + o97 + 0x24u));
		printf("apply-397 done\n");
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()

assert src.count(START) == 1, "apply-396 block marker not found"
a = src.index(START)
src = src[:a] + BLOCK + src[a:]

old = "pcie_mhi_data != 18u && pcie_mhi_data != 19u"
assert src.count(old) == 2, "expected two gates, found %d" % src.count(old)
src = src.replace(old, "pcie_mhi_data != 18u && pcie_mhi_data != 19u && pcie_mhi_data != 20u")

assert src.count("apply-397 done") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-397 ok")
