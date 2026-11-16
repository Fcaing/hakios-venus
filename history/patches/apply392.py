#!/usr/bin/env python3
"""apply-392: does anything fetch ch20 at all?

p429-p432 could not answer it: a TRE whose payload pointer is 0xa0100000 is *inside* the
device's MHI window (MHICTRLBASE 0xa0000000 .. limit 0xb0000000), so even a fetch would not
fault, and an IPCR client is free not to post a TX completion.  And "the firmware put chstate
back" only happens on START_CHAN, so silence there proved nothing either.

The clean discriminator is a payload pointer *outside* the window: 0x80000000.  Any engine
that reads it faults (SYS_ERR / EE change / SMMU).  Order matters: ch20 first, then ch4, then
ch0 as the control that we know fetches.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
START = "\t/* apply-391: "

BLOCK = r'''	/* apply-392: queue a TRE whose payload pointer is outside the MHI window and see who
	 * faults.  ch20 (IPCR TX) first, then ch4 (DIAG), then ch0 (LOOPBACK, known to fetch). */
	if (pcie_mhi_data == 15u && smmu_state == 1 && pcie_dma_extra != 0) {
		uint32_t k92, ci92, o92, r92, e0, m0v;
		printf("apply-392 t0: ee 0x%08x mh 0x%08x\n", rd(bar0.base + 0x128), rd(bar0.base + 0x48));
		for (ci92 = 0; ci92 < 3u; ci92++) {
			uint32_t ch = (ci92 == 0u) ? 20u : ((ci92 == 1u) ? 4u : 0u);
			uint32_t db = (ci92 == 0u) ? 0x3a0u : ((ci92 == 1u) ? 0x320u : 0x300u);
			o92 = ch * 0x2cu;
			r92 = rd(pcie_dma_extra + o92 + 0x0cu);
			printf("apply-392 ch%u: st 0x%08x rbase 0x%08x rp 0x%08x wp 0x%08x db 0x%03x\n",
			    ch, rd(pcie_dma_extra + o92), r92,
			    rd(pcie_dma_extra + o92 + 0x1cu), rd(pcie_dma_extra + o92 + 0x24u), db);
			if (r92 < (uint32_t)PCIE_EXTRA_IOVA ||
			    r92 > (uint32_t)(PCIE_EXTRA_IOVA + 0x1c0000u))
				continue;
			{
				uint32_t off = r92 - (uint32_t)PCIE_EXTRA_IOVA;
				wr(pcie_dma_extra + off + 0x00u, 0x80000000u);
				wr(pcie_dma_extra + off + 0x04u, 0x00000000u);
				wr(pcie_dma_extra + off + 0x08u, 0x00000010u);
				wr(pcie_dma_extra + off + 0x0cu, 0x00020200u);
				wr(pcie_dma_extra + o92 + 0x24u, r92 + 0x10u);
				wr(pcie_dma_extra + o92 + 0x28u, 0u);
				__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + off) : "memory");
				__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + o92) : "memory");
				__asm__ volatile ("dsb sy" : : : "memory");
				wr(bar0.base + db + 4u, 0u);
				wr(bar0.base + db, r92 + 0x10u);
				__asm__ volatile ("dsb sy" : : : "memory");
				e0 = rd(bar0.base + 0x128);
				m0v = rd(bar0.base + 0x48);
				printf("apply-392 ch%u: bad tre queued, ee 0x%08x mh 0x%08x\n", ch, e0, m0v);
				for (k92 = 0; k92 < 30u; k92++) {
					sleep_ms(10);
					if (rd(bar0.base + 0x128) != e0 || (rd(bar0.base + 0x48) & 0x4u) != 0u)
						break;
				}
				printf("apply-392 ch%u: after %u ms ee 0x%08x mh 0x%08x st 0x%08x\n",
				    ch, (k92 + 1u) * 10u, rd(bar0.base + 0x128), rd(bar0.base + 0x48),
				    rd(pcie_dma_extra + o92));
				if (rd(bar0.base + 0x128) != e0)
					break;
			}
		}
		printf("apply-392 done: ee 0x%08x mh 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48));
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()

assert src.count(START) == 1, "apply-391 block marker not found"
a = src.index(START)
src = src[:a] + BLOCK + src[a:]

old = "pcie_mhi_data != 12u && pcie_mhi_data != 13u && pcie_mhi_data != 14u"
assert src.count(old) == 2, "expected two gates, found %d" % src.count(old)
src = src.replace(old, "pcie_mhi_data != 12u && pcie_mhi_data != 13u && pcie_mhi_data != 14u && pcie_mhi_data != 15u")

assert src.count("apply-392 done") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-392 ok")
