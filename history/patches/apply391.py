#!/usr/bin/env python3
"""apply-391: is there a firmware client on ch20/ch21 at all?

p429-p431 proved the host side completely: the same code that makes ch0/ch1 deliver a TRE,
a payload and two TX_EVENTs leaves ch20 (IPCR TX) silent, with its context at chstate 2
(RUNNING) and the doorbell honouring our writes.

So the remaining question is binary: does the firmware own a client on ch20/ch21?  If it does,
it will notice that the host took the channel back to ENABLED and put it back to RUNNING.  If
nothing restores it, nothing on the firmware side is listening and the channel has to be brought
up some other way.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
START = "\t/* apply-390: arm LOOPBACK RX (ch1), send a pattern on ch0, look for the echo. */\n"

BLOCK = r'''	/* apply-391: does the firmware have a client on ch20/ch21?  Force chstate back to
	 * ENABLED and watch whether it is restored to RUNNING, then try one TX TRE on ch20. */
	if (pcie_mhi_data == 14u && smmu_state == 1 && pcie_dma_extra != 0) {
		uint32_t o20 = 20u * 0x2cu, o21 = 21u * 0x2cu, oe1 = 0x2000u + 0x2cu;
		uint32_t k91, st91, v91, seen91, r20, r21, er1base, offe1;
		printf("apply-391 t0: ee 0x%08x mh 0x%08x cfg 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(bar0.base + 0x10));
		printf("apply-391 a ch20: st 0x%08x type 0x%08x eri 0x%08x rbase 0x%08x len 0x%08x rp 0x%08x wp 0x%08x\n",
		    rd(pcie_dma_extra + o20), rd(pcie_dma_extra + o20 + 0x04u),
		    rd(pcie_dma_extra + o20 + 0x08u), rd(pcie_dma_extra + o20 + 0x0cu),
		    rd(pcie_dma_extra + o20 + 0x14u), rd(pcie_dma_extra + o20 + 0x1cu),
		    rd(pcie_dma_extra + o20 + 0x24u));
		printf("apply-391 a ch21: st 0x%08x type 0x%08x eri 0x%08x rbase 0x%08x len 0x%08x rp 0x%08x wp 0x%08x\n",
		    rd(pcie_dma_extra + o21), rd(pcie_dma_extra + o21 + 0x04u),
		    rd(pcie_dma_extra + o21 + 0x08u), rd(pcie_dma_extra + o21 + 0x0cu),
		    rd(pcie_dma_extra + o21 + 0x14u), rd(pcie_dma_extra + o21 + 0x1cu),
		    rd(pcie_dma_extra + o21 + 0x24u));

		/* ch20: take the channel back to ENABLED, keep its ring, and see who notices. */
		v91 = rd(pcie_dma_extra + o20);
		st91 = v91 & 0xffu;
		wr(pcie_dma_extra + o20, (v91 & 0xffffff00u) | 1u);
		__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + o20) : "memory");
		__asm__ volatile ("dsb sy" : : : "memory");
		printf("apply-391 b ch20: forced st 0x%08x -> 0x%08x\n", st91, rd(pcie_dma_extra + o20) & 0xffu);
		seen91 = 0u;
		for (k91 = 0; k91 < 40u; k91++) {
			sleep_ms(10);
			st91 = rd(pcie_dma_extra + o20) & 0xffu;
			if (st91 != 1u) {
				printf("apply-391 c ch20: st 0x%08x after %u ms\n", st91, (k91 + 1u) * 10u);
				seen91 = 1u;
				break;
			}
		}
		if (seen91 == 0u)
			printf("apply-391 c ch20: still 0x%08x after 400 ms\n", rd(pcie_dma_extra + o20) & 0xffu);

		/* ch21: same question for the receive direction. */
		v91 = rd(pcie_dma_extra + o21);
		st91 = v91 & 0xffu;
		wr(pcie_dma_extra + o21, (v91 & 0xffffff00u) | 1u);
		__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + o21) : "memory");
		__asm__ volatile ("dsb sy" : : : "memory");
		printf("apply-391 d ch21: forced st 0x%08x -> 0x%08x\n", st91, rd(pcie_dma_extra + o21) & 0xffu);
		seen91 = 0u;
		for (k91 = 0; k91 < 40u; k91++) {
			sleep_ms(10);
			st91 = rd(pcie_dma_extra + o21) & 0xffu;
			if (st91 != 1u) {
				printf("apply-391 e ch21: st 0x%08x after %u ms\n", st91, (k91 + 1u) * 10u);
				seen91 = 1u;
				break;
			}
		}
		if (seen91 == 0u)
			printf("apply-391 e ch21: still 0x%08x after 400 ms\n", rd(pcie_dma_extra + o21) & 0xffu);

		/* Whatever the answer, also try one clean TX TRE on ch20 and dump er1. */
		r20 = rd(pcie_dma_extra + o20 + 0x0cu);
		r21 = rd(pcie_dma_extra + o21 + 0x0cu);
		er1base = rd(pcie_dma_extra + oe1 + 0x0cu);
		printf("apply-391 f ch20 st 0x%08x rbase 0x%08x rp 0x%08x wp 0x%08x | er1 base 0x%08x rp 0x%08x wp 0x%08x\n",
		    rd(pcie_dma_extra + o20), r20, rd(pcie_dma_extra + o20 + 0x1cu),
		    rd(pcie_dma_extra + o20 + 0x24u), er1base,
		    rd(pcie_dma_extra + oe1 + 0x1cu), rd(pcie_dma_extra + oe1 + 0x24u));
		if (r20 >= (uint32_t)PCIE_EXTRA_IOVA && r20 <= (uint32_t)(PCIE_EXTRA_IOVA + 0x1c0000u)) {
			uint32_t off20 = r20 - (uint32_t)PCIE_EXTRA_IOVA;
			uint32_t i91;
			for (i91 = 0; i91 < 4u; i91++)
				wr(pcie_dma_extra + 0x1f0000u + i91 * 4u, 0x49504352u + i91);
			wr(pcie_dma_extra + off20 + 0x00u, (uint32_t)(PCIE_EXTRA_IOVA + 0x1f0000u));
			wr(pcie_dma_extra + off20 + 0x04u, 0x00000000u);
			wr(pcie_dma_extra + off20 + 0x08u, 0x00000010u);
			wr(pcie_dma_extra + off20 + 0x0cu, 0x00020200u);
			wr(pcie_dma_extra + o20 + 0x24u, r20 + 0x10u);
			wr(pcie_dma_extra + o20 + 0x28u, 0u);
			__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + 0x1f0000u) : "memory");
			__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + off20) : "memory");
			__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + o20) : "memory");
			__asm__ volatile ("dsb sy" : : : "memory");
			printf("apply-391 g ch20: tre queued, wp 0x%08x, ringing 0x3a0\n",
			    rd(pcie_dma_extra + o20 + 0x24u));
			wr(bar0.base + 0x3a0u + 4u, 0u);
			wr(bar0.base + 0x3a0u, r20 + 0x10u);
			__asm__ volatile ("dsb sy" : : : "memory");
			seen91 = 0u;
			if (er1base >= (uint32_t)PCIE_EXTRA_IOVA &&
			    er1base <= (uint32_t)(PCIE_EXTRA_IOVA + 0x1c0000u)) {
				offe1 = er1base - (uint32_t)PCIE_EXTRA_IOVA;
				for (k91 = 0; k91 < 60u; k91++) {
					sleep_ms(10);
					for (i91 = 0; i91 < 8u; i91++)
						if (rd(pcie_dma_extra + offe1 + i91 * 16u + 12u) != 0u) {
							seen91 = 1u;
							break;
						}
					if (seen91 != 0u || rd(bar0.base + 0x128) != 2u)
						break;
				}
				for (i91 = 0; i91 < 6u; i91++)
					printf("apply-391 i er1[%u]: %08x %08x %08x %08x\n", i91,
					    rd(pcie_dma_extra + offe1 + i91 * 16u),
					    rd(pcie_dma_extra + offe1 + i91 * 16u + 4u),
					    rd(pcie_dma_extra + offe1 + i91 * 16u + 8u),
					    rd(pcie_dma_extra + offe1 + i91 * 16u + 12u));
			} else {
				printf("apply-391 i er1 base 0x%08x not in window\n", er1base);
			}
			printf("apply-391 h end: event %u ee 0x%08x mh 0x%08x ch20 st 0x%08x\n",
			    seen91, rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(pcie_dma_extra + o20));
		} else {
			printf("apply-391 g ch20: rbase 0x%08x not in our window, no TRE\n", r20);
		}
		printf("apply-391 done\n");
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()

assert src.count(START) == 1, "apply-390 block marker not found"
a = src.index(START)
src = src[:a] + BLOCK + src[a:]

old = "pcie_mhi_data != 12u && pcie_mhi_data != 13u"
assert src.count(old) == 2, "expected two gates, found %d" % src.count(old)
src = src.replace(old, "pcie_mhi_data != 12u && pcie_mhi_data != 13u && pcie_mhi_data != 14u")

assert src.count("apply-391 done") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-391 ok")
