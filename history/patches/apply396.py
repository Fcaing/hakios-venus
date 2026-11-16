#!/usr/bin/env python3
"""apply-396 (data=19): does the channel doorbell need a device-wake pulse first?

p438 showed there is no RDDM dump to be had (BHIE RX armed correctly, nothing delivered; the
BHIE window reads back noise in AMSS), so the firmware will not testify.  What is left is the
one asymmetry we have never varied: every channel doorbell we have rung was rung on its own,
while the vendor's own mhi_ring_chan_db path is only reached from mhi_pm_m0_transition, which
starts with wake_get() -- and this part advertises "mhi,m2-no-db-access", i.e. the doorbell
block is only reachable while the device is awake.

So: pulse MHI_DEV_WAKE_DB (0x300 + 8*127 = 0x6f8, write 1 then 0) and then ring the channel,
with the bad-pointer TRE as the detector.  ch0 is the control (it always fetches), ch20 is the
suspect, ch21 is the receive channel.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
START = "\t/* apply-395: "

BLOCK = r'''	/* apply-396: wake pulse before the channel doorbell, bad-TRE detector. */
	if (pcie_mhi_data == 19u && smmu_state == 1 && pcie_dma_extra != 0) {
		uint32_t k96, w96, o96, ch96, st96, wp96, rb96, ro96;
		uint64_t bad96 = 0x80000000ull;

		printf("apply-396 t0: ee 0x%08x mh 0x%08x wake 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(bar0.base + 0x6f8));
		for (k96 = 0; k96 < 3u; k96++) {
			ch96 = (k96 == 0u) ? 20u : ((k96 == 1u) ? 0u : 21u);
			o96 = ch96 * 0x2cu;
			rb96 = rd(pcie_dma_extra + o96 + 0x0cu);
			wp96 = rd(pcie_dma_extra + o96 + 0x24u);
			printf("apply-396 ch%u before: st 0x%08x eri 0x%08x rbase 0x%08x wp 0x%08x\n",
			    ch96, rd(pcie_dma_extra + o96), rd(pcie_dma_extra + o96 + 0x08u), rb96, wp96);
			/* one TRE at wp: payload far outside the MHI window, so a fetch must fault.
			 * The ring's CPU-side address is (iova - PCIE_EXTRA_IOVA), not the context
			 * offset -- getting that wrong writes the TRE over the next context. */
			ro96 = wp96 - (uint32_t)PCIE_EXTRA_IOVA;
			wr(pcie_dma_extra + ro96, (uint32_t)bad96);
			wr(pcie_dma_extra + ro96 + 4u, 0u);
			wr(pcie_dma_extra + ro96 + 8u, (0x1000u << 16) | 0x0200u);
			wr(pcie_dma_extra + ro96 + 12u, (ch96 << 24) | (2u << 16));
			/* wake the device first, the way wake_get()/wake_put() bracket the vendor path */
			wr(bar0.base + 0x6f8, 1u);
			sleep_ms(2);
			wr(bar0.base + 0x6f8, 0u);
			/* publish the new wp, then ring the channel doorbell */
			wr(pcie_dma_extra + o96 + 0x24u, wp96 + 16u);
			wr(bar0.base + 0x300 + ch96 * 8u + 4u, 0u);
			wr(bar0.base + 0x300 + ch96 * 8u, wp96 + 16u);
			for (w96 = 0; w96 < 20u; w96++) {
				sleep_ms(15);
				st96 = rd(pcie_dma_extra + o96);
				if ((st96 & 0xffu) != 0x02u || rd(bar0.base + 0x128) != 2u)
					break;
			}
			printf("apply-396 ch%u after %u ms: st 0x%08x ee 0x%08x mh 0x%08x\n",
			    ch96, (w96 + 1u) * 15u, st96, rd(bar0.base + 0x128), rd(bar0.base + 0x48));
		}
		printf("apply-396 done\n");
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()

assert src.count(START) == 1, "apply-395 block marker not found"
a = src.index(START)
src = src[:a] + BLOCK + src[a:]

old = "pcie_mhi_data != 16u && pcie_mhi_data != 18u"
assert src.count(old) == 2, "expected two gates, found %d" % src.count(old)
src = src.replace(old, "pcie_mhi_data != 16u && pcie_mhi_data != 18u && pcie_mhi_data != 19u")

assert src.count("apply-396 done") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-396 ok")
