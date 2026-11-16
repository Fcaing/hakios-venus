#!/usr/bin/env python3
"""apply-389: the same host code, three channels - LOOPBACK (ch0), DIAG (ch4), IPCR (ch20).

p429 showed ch1 (LOOPBACK, device->host) is the only channel that reacted to a doorbell:
it went from RUNNING to ERROR after we handed it an unmapped buffer.  So the firmware's
MHI engine does service some channel doorbells.  This round sends a *valid* TRE to the TX
side of three different channels with identical host code, so any difference is on the
firmware side, not in our programming sequence.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
START = "\t/* apply-388: ring every running channel's doorbell with a bad TRE (offsets only). */\n"
MARK = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-389: one valid TRE each on LOOPBACK TX (ch0), DIAG TX (ch4), IPCR TX (ch20). */
	if (pcie_mhi_data == 12u && smmu_state == 1 && pcie_dma_extra != 0) {
		uint32_t i89, ch = 0, o89, rbase89, off89, t89, ee89, mh89, st89, got89, k89;
		printf("apply-389 t0: ee 0x%08x mh 0x%08x ctrl 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(bar0.base + 0x38));
		for (i89 = 0; i89 < 3u; i89++) {
			if (i89 == 0u) {
				ch = 0u;
			} else if (i89 == 1u) {
				ch = 4u;
			} else {
				ch = 20u;
			}
			o89 = ch * 0x2cu;
			st89 = rd(pcie_dma_extra + o89);
			rbase89 = rd(pcie_dma_extra + o89 + 0x0cu);
			printf("apply-389 a ch%u: st 0x%08x type 0x%08x eri 0x%08x rbase 0x%08x len 0x%08x rp 0x%08x wp 0x%08x\n",
			    ch, st89, rd(pcie_dma_extra + o89 + 0x04u), rd(pcie_dma_extra + o89 + 0x08u),
			    rbase89, rd(pcie_dma_extra + o89 + 0x14u),
			    rd(pcie_dma_extra + o89 + 0x1cu), rd(pcie_dma_extra + o89 + 0x24u));
			if ((st89 & 0xffu) != 2u || rbase89 < (uint32_t)PCIE_EXTRA_IOVA ||
			    rbase89 > (uint32_t)(PCIE_EXTRA_IOVA + 0x1c0000u)) {
				printf("apply-389 b ch%u: not running or outside our window, skipped\n", ch);
				continue;
			}
			off89 = rbase89 - (uint32_t)PCIE_EXTRA_IOVA;
			/* a payload buffer of our own, well away from the rings */
			for (k89 = 0; k89 < 8u; k89++) {
				wr(pcie_dma_extra + 0x200000u + k89 * 4u, 0x4f4f4c48u + k89);
			}
			wr(pcie_dma_extra + off89 + 0x00u, (uint32_t)(PCIE_EXTRA_IOVA + 0x200000u));
			wr(pcie_dma_extra + off89 + 0x04u, 0x00000000u);
			wr(pcie_dma_extra + off89 + 0x08u, 0x00000020u);
			wr(pcie_dma_extra + off89 + 0x0cu, 0x00020200u);
			wr(pcie_dma_extra + o89 + 0x24u, rbase89 + 0x10u);
			wr(pcie_dma_extra + o89 + 0x28u, 0u);
			__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + off89) : "memory");
			__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + 0x200000u) : "memory");
			__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + o89) : "memory");
			__asm__ volatile ("dsb sy" : : : "memory");
			printf("apply-389 c ch%u: tre ptr 0x%08x len 0x20 flags 0x00020200 wp 0x%08x, ringing 0x%08x\n",
			    ch, (uint32_t)(PCIE_EXTRA_IOVA + 0x200000u), rd(pcie_dma_extra + o89 + 0x24u),
			    0x300u + ch * 8u);
			ee89 = rd(bar0.base + 0x128);
			mh89 = rd(bar0.base + 0x48);
			wr(bar0.base + 0x300 + ch * 8u + 4u, 0u);
			wr(bar0.base + 0x300 + ch * 8u, rbase89 + 0x10u);
			__asm__ volatile ("dsb sy" : : : "memory");
			got89 = 0;
			for (t89 = 0; t89 < 300u; t89++) {
				sleep_ms(1);
				if (t89 == 100u || t89 == 200u) {
					printf("apply-389 d ch%u t=%u ms: st 0x%08x rp 0x%08x wp 0x%08x\n", ch, t89,
					    rd(pcie_dma_extra + o89), rd(pcie_dma_extra + o89 + 0x1cu),
					    rd(pcie_dma_extra + o89 + 0x24u));
				}
				if (rd(bar0.base + 0x128) != ee89 || rd(bar0.base + 0x48) != mh89) {
					got89 = 1;
					printf("apply-389 e ch%u STATE CHANGE at %u ms: ee 0x%08x mh 0x%08x\n",
					    ch, t89, rd(bar0.base + 0x128), rd(bar0.base + 0x48));
					break;
				}
			}
			printf("apply-389 f ch%u: done got 0x%08x st 0x%08x rp 0x%08x wp 0x%08x\n", ch, got89,
			    rd(pcie_dma_extra + o89), rd(pcie_dma_extra + o89 + 0x1cu),
			    rd(pcie_dma_extra + o89 + 0x24u));
			printf("apply-389 g er0: %08x %08x %08x %08x | %08x %08x %08x %08x\n",
			    rd(pcie_dma_extra + 0x4000u), rd(pcie_dma_extra + 0x4004u),
			    rd(pcie_dma_extra + 0x4008u), rd(pcie_dma_extra + 0x400cu),
			    rd(pcie_dma_extra + 0x4010u), rd(pcie_dma_extra + 0x4014u),
			    rd(pcie_dma_extra + 0x4018u), rd(pcie_dma_extra + 0x401cu));
			printf("apply-389 h er1: %08x %08x %08x %08x | %08x %08x %08x %08x\n",
			    rd(pcie_dma_extra + 0x5000u), rd(pcie_dma_extra + 0x5004u),
			    rd(pcie_dma_extra + 0x5008u), rd(pcie_dma_extra + 0x500cu),
			    rd(pcie_dma_extra + 0x5010u), rd(pcie_dma_extra + 0x5014u),
			    rd(pcie_dma_extra + 0x5018u), rd(pcie_dma_extra + 0x501cu));
			printf("apply-389 i buf: %08x %08x %08x %08x\n",
			    rd(pcie_dma_extra + 0x200000u), rd(pcie_dma_extra + 0x200004u),
			    rd(pcie_dma_extra + 0x200008u), rd(pcie_dma_extra + 0x20000cu));
		}
		printf("apply-389 j end: ee 0x%08x mh 0x%08x\n", rd(bar0.base + 0x128), rd(bar0.base + 0x48));
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()

assert src.count(START) == 1, "apply-388 block marker not found"
a = src.index(START)
b = src.index(MARK, a)
src = src[:a] + BLOCK + src[b:]

old = "pcie_mhi_data != 11u"
assert src.count(old) == 2, "expected two gates, found %d" % src.count(old)
src = src.replace(old, "pcie_mhi_data != 11u && pcie_mhi_data != 12u")

assert "apply-389" not in src.replace(BLOCK, ""), "apply-389 is already in the source"
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-389 ok")
