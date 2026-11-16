#!/usr/bin/env python3
"""apply-395 (data=18): arm BHIE RX, then force the device into RDDM and take the dump.

p435 showed the firmware sits in AMSS with the IPCR channels untouched - no retry loop, no
progress.  The only witness left is the firmware's own crash/assert record, and the way to
get it is the one vendor mhi_rddm_prepare() uses: point BHIE RX at a host buffer, give it a
sequence id, then push the device into RDDM.

Registers (all relative to the BHIE block at bar0 + 0x224):
  0x60 RXVECADDR_LOW, 0x64 RXVECADDR_HIGH, 0x68 RXVECSIZE, 0x70 RXVECDB (seq), 0x78 RXVECSTATUS
RXVECSTATUS: status is bits 30-31, 2 = XFER_COMPL, 3 = ERROR, seq is bits 0-29.

The buffer sits at PCIE_EXTRA_IOVA + 0x600000 (the firmware image ends around +0x520000 and the
extra block is 8 MB), so it is already inside the SMMU window and CPU-readable through
pcie_dma_extra.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
START = "\t/* apply-393: "

BLOCK = r'''	/* apply-395: arm BHIE RX, force RDDM, take whatever the firmware has to say. */
	if (pcie_mhi_data == 18u && smmu_state == 1 && pcie_dma_extra != 0) {
		uint64_t rddm_iova = PCIE_EXTRA_IOVA + 0x600000ull;
		uint32_t rddm_off = 0x600000u;
		uint32_t rddm_len = 0x200000u;
		uint32_t i95, st95 = 0, seq95 = 0x12345u, seen95 = 0;
		uint32_t last95 = 0xffffffffu;

		printf("apply-395 t0: ee 0x%08x mh 0x%08x bhie 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(bar0.base + 0x2c));
		/* a known pattern, so that a silent non-delivery is obvious */
		for (i95 = 0; i95 < 64u; i95++)
			wr(pcie_dma_extra + rddm_off + i95 * 4u, 0x5a5a0000u | i95);
		/* mhi_rddm_prepare(): high half first, then low, then size, then the doorbell */
		wr(bar0.base + 0x224 + 0x64u, (uint32_t)(rddm_iova >> 32));
		wr(bar0.base + 0x224 + 0x60u, (uint32_t)rddm_iova);
		wr(bar0.base + 0x224 + 0x68u, rddm_len);
		wr(bar0.base + 0x224 + 0x70u, seq95);
		printf("apply-395 armed: addr 0x%08x/%08x size 0x%08x seq 0x%08x status 0x%08x\n",
		    rd(bar0.base + 0x224 + 0x64u), rd(bar0.base + 0x224 + 0x60u),
		    rd(bar0.base + 0x224 + 0x68u), rd(bar0.base + 0x224 + 0x70u),
		    rd(bar0.base + 0x224 + 0x78u));

		wr(bar0.base + 0xb0, 1u);
		for (i95 = 0; i95 < 400u; i95++) {
			sleep_ms(1);
			st95 = rd(bar0.base + 0x224 + 0x78u);
			if (st95 != last95) {
				printf("apply-395 t=%u ms: rxstat 0x%08x (status %u seq 0x%08x) ee 0x%08x\n",
				    i95, st95, st95 >> 30, st95 & 0x3fffffffu, rd(bar0.base + 0x128));
				last95 = st95;
				if ((st95 >> 30) == 2u || (st95 >> 30) == 3u) {
					seen95 = 1;
					break;
				}
			}
		}
		printf("apply-395 pinned attempt: wr 0xb0 again\n");
		wr(bar0.base + 0xb0, 1u);
		for (i95 = 0; i95 < 2000u && seen95 == 0u; i95++) {
			sleep_ms(1);
			st95 = rd(bar0.base + 0x224 + 0x78u);
			if (st95 != last95) {
				printf("apply-395 p t=%u ms: rxstat 0x%08x (status %u seq 0x%08x) ee 0x%08x\n",
				    i95, st95, st95 >> 30, st95 & 0x3fffffffu, rd(bar0.base + 0x128));
				last95 = st95;
				if ((st95 >> 30) == 2u || (st95 >> 30) == 3u) {
					seen95 = 1;
					break;
				}
			}
		}
		printf("apply-395 end: delivered 0x%u rxstat 0x%08x ee 0x%08x mh 0x%08x b0 0x%08x\n",
		    seen95, rd(bar0.base + 0x224 + 0x78u), rd(bar0.base + 0x128),
		    rd(bar0.base + 0x48), rd(bar0.base + 0xb0));
		for (i95 = 0; i95 < 16u; i95++)
			printf("apply-395 buf[%02u] 0x%08x\n", i95, rd(pcie_dma_extra + rddm_off + i95 * 4u));
		printf("apply-395 done\n");
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()

assert src.count(START) == 1, "apply-393 block marker not found"
a = src.index(START)
src = src[:a] + BLOCK + src[a:]

old = "pcie_mhi_data != 15u && pcie_mhi_data != 16u"
assert src.count(old) == 2, "expected two gates, found %d" % src.count(old)
src = src.replace(old, "pcie_mhi_data != 15u && pcie_mhi_data != 16u && pcie_mhi_data != 18u")

assert src.count("apply-395 done") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-395 ok")
