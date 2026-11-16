#!/usr/bin/env python3
"""apply-390: close the loop - arm LOOPBACK RX (ch1) with two buffers, send on ch0, look
for the echo.

p430 proved the host side: ch0's TRE was fetched, the 0x20-byte payload at 0xa0400000 was
read, and a TX_EVENT (type 0x22) came back on er1.  ch4 (DIAG) and ch20 (IPCR) stayed
silent with the very same code, so the difference is on the firmware side.

Now give the device somewhere to write: two RX buffers on ch1, then the same ch0 send.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
START = "\t/* apply-389: one valid TRE each on LOOPBACK TX (ch0), DIAG TX (ch4), IPCR TX (ch20). */\n"
MARK = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-390: arm LOOPBACK RX (ch1), send a pattern on ch0, look for the echo. */
	if (pcie_mhi_data == 13u && smmu_state == 1 && pcie_dma_extra != 0) {
		uint32_t i90, o90, o1, r1, off1, t90, st1, k90, ev90;
		printf("apply-390 t0: ee 0x%08x mh 0x%08x\n", rd(bar0.base + 0x128), rd(bar0.base + 0x48));
		for (i90 = 0; i90 < 4u; i90++) {
			wr(pcie_dma_extra + 0x1d0000u + i90 * 4u, 0x534f494bu + i90);
			wr(pcie_dma_extra + 0x1e0000u + i90 * 4u, 0xdead0000u + i90);
			wr(pcie_dma_extra + 0x1f0000u + i90 * 4u, 0xbeef0000u + i90);
		}
		/* ch1: two RX buffers, announced through the ring and the doorbell */
		o1 = 1u * 0x2cu;
		r1 = rd(pcie_dma_extra + o1 + 0x0cu);
		st1 = rd(pcie_dma_extra + o1);
		printf("apply-390 a ch1: st 0x%08x type 0x%08x eri 0x%08x rbase 0x%08x len 0x%08x rp 0x%08x wp 0x%08x\n",
		    st1, rd(pcie_dma_extra + o1 + 0x04u), rd(pcie_dma_extra + o1 + 0x08u), r1,
		    rd(pcie_dma_extra + o1 + 0x14u), rd(pcie_dma_extra + o1 + 0x1cu),
		    rd(pcie_dma_extra + o1 + 0x24u));
		if ((st1 & 0xffu) == 2u && r1 >= (uint32_t)PCIE_EXTRA_IOVA &&
		    r1 <= (uint32_t)(PCIE_EXTRA_IOVA + 0x1c0000u)) {
			off1 = r1 - (uint32_t)PCIE_EXTRA_IOVA;
			wr(pcie_dma_extra + off1 + 0x00u, (uint32_t)(PCIE_EXTRA_IOVA + 0x1e0000u));
			wr(pcie_dma_extra + off1 + 0x04u, 0x00000000u);
			wr(pcie_dma_extra + off1 + 0x08u, 0x00000100u);
			wr(pcie_dma_extra + off1 + 0x0cu, 0x00020200u);
			wr(pcie_dma_extra + off1 + 0x10u, (uint32_t)(PCIE_EXTRA_IOVA + 0x1f0000u));
			wr(pcie_dma_extra + off1 + 0x14u, 0x00000000u);
			wr(pcie_dma_extra + off1 + 0x18u, 0x00000100u);
			wr(pcie_dma_extra + off1 + 0x1cu, 0x00020200u);
			wr(pcie_dma_extra + o1 + 0x24u, r1 + 0x20u);
			wr(pcie_dma_extra + o1 + 0x28u, 0u);
			__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + off1) : "memory");
			__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + 0x1e0000u) : "memory");
			__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + o1) : "memory");
			__asm__ volatile ("dsb sy" : : : "memory");
			printf("apply-390 b ch1: two buffers at 0x%08x/0x%08x wp 0x%08x, ringing 0x308\n",
			    (uint32_t)(PCIE_EXTRA_IOVA + 0x1e0000u), (uint32_t)(PCIE_EXTRA_IOVA + 0x1f0000u),
			    rd(pcie_dma_extra + o1 + 0x24u));
			wr(bar0.base + 0x308u + 4u, 0u);
			wr(bar0.base + 0x308u, r1 + 0x20u);
			__asm__ volatile ("dsb sy" : : : "memory");
		} else {
			printf("apply-390 b ch1: not usable (st 0x%08x rbase 0x%08x)\n", st1, r1);
		}
		/* ch0: send the pattern */
		o90 = 0u;
		st1 = rd(pcie_dma_extra + o90);
		r1 = rd(pcie_dma_extra + o90 + 0x0cu);
		printf("apply-390 c ch0: st 0x%08x rbase 0x%08x wp 0x%08x\n", st1, r1,
		    rd(pcie_dma_extra + o90 + 0x24u));
		if ((st1 & 0xffu) == 2u && r1 >= (uint32_t)PCIE_EXTRA_IOVA &&
		    r1 <= (uint32_t)(PCIE_EXTRA_IOVA + 0x1c0000u)) {
			off1 = r1 - (uint32_t)PCIE_EXTRA_IOVA;
			wr(pcie_dma_extra + off1 + 0x00u, (uint32_t)(PCIE_EXTRA_IOVA + 0x1d0000u));
			wr(pcie_dma_extra + off1 + 0x04u, 0x00000000u);
			wr(pcie_dma_extra + off1 + 0x08u, 0x00000010u);
			wr(pcie_dma_extra + off1 + 0x0cu, 0x00020200u);
			wr(pcie_dma_extra + o90 + 0x24u, r1 + 0x10u);
			wr(pcie_dma_extra + o90 + 0x28u, 0u);
			__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + off1) : "memory");
			__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + 0x1d0000u) : "memory");
			__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + o90) : "memory");
			__asm__ volatile ("dsb sy" : : : "memory");
			printf("apply-390 d ch0: tre ptr 0x%08x len 0x10 wp 0x%08x, ringing 0x300\n",
			    (uint32_t)(PCIE_EXTRA_IOVA + 0x1d0000u), rd(pcie_dma_extra + o90 + 0x24u));
			wr(bar0.base + 0x300u + 4u, 0u);
			wr(bar0.base + 0x300u, r1 + 0x10u);
			__asm__ volatile ("dsb sy" : : : "memory");
		}
		ev90 = 0;
		for (t90 = 0; t90 < 400u; t90++) {
			sleep_ms(1);
			if (t90 == 150u || t90 == 300u) {
				printf("apply-390 e t=%u ms: ch0 st 0x%08x | ch1 st 0x%08x rp 0x%08x wp 0x%08x | er1 %08x %08x %08x %08x | %08x %08x %08x %08x\n",
				    t90, rd(pcie_dma_extra + 0x00u), rd(pcie_dma_extra + o1),
				    rd(pcie_dma_extra + o1 + 0x1cu), rd(pcie_dma_extra + o1 + 0x24u),
				    rd(pcie_dma_extra + 0x5000u), rd(pcie_dma_extra + 0x5004u),
				    rd(pcie_dma_extra + 0x5008u), rd(pcie_dma_extra + 0x500cu),
				    rd(pcie_dma_extra + 0x5010u), rd(pcie_dma_extra + 0x5014u),
				    rd(pcie_dma_extra + 0x5018u), rd(pcie_dma_extra + 0x501cu));
			}
			if (rd(pcie_dma_extra + 0x1e0000u) != 0xdead0000u ||
			    rd(pcie_dma_extra + 0x1f0000u) != 0xbeef0000u) {
				ev90 = 1;
				printf("apply-390 f ECHO at %u ms: a %08x %08x %08x %08x | b %08x %08x %08x %08x\n",
				    t90, rd(pcie_dma_extra + 0x1e0000u), rd(pcie_dma_extra + 0x1e0004u),
				    rd(pcie_dma_extra + 0x1e0008u), rd(pcie_dma_extra + 0x1e000cu),
				    rd(pcie_dma_extra + 0x1f0000u), rd(pcie_dma_extra + 0x1f0004u),
				    rd(pcie_dma_extra + 0x1f0008u), rd(pcie_dma_extra + 0x1f000cu));
				break;
			}
		}
		printf("apply-390 g end: echo 0x%08x ee 0x%08x mh 0x%08x | er1 %08x %08x %08x %08x\n",
		    ev90, rd(bar0.base + 0x128), rd(bar0.base + 0x48),
		    rd(pcie_dma_extra + 0x5000u), rd(pcie_dma_extra + 0x5004u),
		    rd(pcie_dma_extra + 0x5008u), rd(pcie_dma_extra + 0x500cu));
		for (k90 = 0; k90 < 4u; k90++) {
			printf("apply-390 h slot%u er1: %08x %08x %08x %08x\n", k90,
			    rd(pcie_dma_extra + 0x5000u + k90 * 0x10u),
			    rd(pcie_dma_extra + 0x5000u + k90 * 0x10u + 4u),
			    rd(pcie_dma_extra + 0x5000u + k90 * 0x10u + 8u),
			    rd(pcie_dma_extra + 0x5000u + k90 * 0x10u + 0xcu));
		}
		printf("apply-390 i ch1 after: st 0x%08x rp 0x%08x wp 0x%08x\n",
		    rd(pcie_dma_extra + o1), rd(pcie_dma_extra + o1 + 0x1cu), rd(pcie_dma_extra + o1 + 0x24u));
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()

assert src.count(START) == 1, "apply-389 block marker not found"
a = src.index(START)
b = src.index(MARK, a)
src = src[:a] + BLOCK + src[b:]

old = "pcie_mhi_data != 12u"
assert src.count(old) == 2, "expected two gates, found %d" % src.count(old)
src = src.replace(old, "pcie_mhi_data != 12u && pcie_mhi_data != 13u")

assert "apply-390" not in src.replace(BLOCK, ""), "apply-390 is already in the source"
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-390 ok")
