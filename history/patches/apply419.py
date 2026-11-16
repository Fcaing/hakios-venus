#!/usr/bin/env python3
"""apply-419: the ipcr ring, tried after the settle window.

apply-418 showed the command ring answers normally two seconds after M0 (a START_CHAN came
back as CMD_COMPLETION code 1 instead of asserting), so every earlier doorbell test was fired
inside a window where the firmware was not ready.  Now do the real thing: wait for the settle,
then queue a TRE on ch20 and ring its doorbell, three times, and read the event ring after.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-419: TRE + doorbell on ch20, two seconds after M0. */
	if (pcie_mhi_data == 39u && smmu_state == 1 && pcie_dma_extra != 0 &&
	    rd(bar0.base + 0x128) == 2u) {
		uint32_t i419, a419, off419, cwp419, st419, wp419, er1rp;
		vm_offset_t t419;

		printf("apply-419 a: ee 0x%08x mh 0x%08x ch20 0x%08x ch21 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48),
		    rd(pcie_dma_extra + 20u * 0x2cu), rd(pcie_dma_extra + 21u * 0x2cu));
		for (i419 = 0; i419 < 20u; i419++)
			sleep_ms(100);
		printf("apply-419 b: settled ee 0x%08x mh 0x%08x ch20 0x%08x rp 0x%08x wp 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(pcie_dma_extra + 20u * 0x2cu),
		    rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu), rd(pcie_dma_extra + 20u * 0x2cu + 0x24u));

		for (a419 = 0; a419 < 3u; a419++) {
			cwp419 = rd(pcie_dma_extra + 20u * 0x2cu + 0x24u);
			st419 = rd(pcie_dma_extra + 20u * 0x2cu);
			if (cwp419 < PCIE_EXTRA_IOVA || cwp419 >= PCIE_EXTRA_IOVA + PCIE_EXTRA_SIZE) {
				printf("apply-419 c: attempt %u wp 0x%08x outside\n", a419, cwp419);
				break;
			}
			t419 = pcie_dma_extra + (cwp419 - (uint32_t)PCIE_EXTRA_IOVA);
			wr(t419 + 0x00u, (uint32_t)(PCIE_EXTRA_IOVA + 0x3a0000u));
			wr(t419 + 0x04u, 0u);
			wr(t419 + 0x08u, 0x00000020u);
			wr(t419 + 0x0cu, 0x00020200u);
			__asm__ __volatile__("dc civac, %0" :: "r"(t419) : "memory");
			__asm__ __volatile__("dsb sy" ::: "memory");
			wr(pcie_dma_extra + 20u * 0x2cu + 0x24u, cwp419 + 0x10u);
			wr(bar0.base + 0x300u + 20u * 8u + 4u, 0u);
			wr(bar0.base + 0x300u + 20u * 8u, cwp419 + 0x10u);
			printf("apply-419 d: attempt %u tre at 0x%08x rung 0x3a0 <- 0x%08x (st 0x%08x)\n",
			    a419, cwp419, cwp419 + 0x10u, st419);

			er1rp = rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x1cu);
			for (i419 = 0; i419 < 100u; i419++) {
				sleep_ms(3);
				if (rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x1cu) != er1rp ||
				    rd(bar0.base + 0x48) != 0x00000201u)
					break;
			}
			printf("apply-419 e: attempt %u after %u ms ch20 0x%08x rp 0x%08x wp 0x%08x er1 rp 0x%08x wp 0x%08x ee 0x%08x mh 0x%08x\n",
			    a419, i419 * 3u, rd(pcie_dma_extra + 20u * 0x2cu),
			    rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu), rd(pcie_dma_extra + 20u * 0x2cu + 0x24u),
			    rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x1cu), rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x24u),
			    rd(bar0.base + 0x128), rd(bar0.base + 0x48));
			wp419 = rd(pcie_dma_extra + 20u * 0x2cu + 0x24u);
			if (wp419 != cwp419 + 0x10u)
				printf("apply-419 f: wp moved on its own to 0x%08x\n", wp419);
		}
		for (off419 = 0; off419 < 6u; off419++) {
			uint32_t o = 0x5000u + off419 * 16u;
			printf("apply-419 g: er1[%u] %08x %08x %08x %08x\n", off419,
			    rd(pcie_dma_extra + o + 0x0u), rd(pcie_dma_extra + o + 0x4u),
			    rd(pcie_dma_extra + o + 0x8u), rd(pcie_dma_extra + o + 0xcu));
		}
		printf("apply-419 h: payload %08x %08x %08x %08x\n",
		    rd(pcie_dma_extra + 0x3a0000u), rd(pcie_dma_extra + 0x3a0004u),
		    rd(pcie_dma_extra + 0x3a0008u), rd(pcie_dma_extra + 0x3a000cu));
		printf("apply-419 i: end ee 0x%08x mh 0x%08x\n", rd(bar0.base + 0x128), rd(bar0.base + 0x48));
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1
assert "apply-419" not in src

a = "pcie_mhi_data != 38u && pcie_chanstart != 0"
assert src.count(a) == 1
src = src.replace(a, "pcie_mhi_data != 38u && pcie_mhi_data != 39u && pcie_chanstart != 0")
b = "pcie_mhi_data != 38u) wr(pcie_dma_extra + 20 * 0x2c"
assert src.count(b) == 1
src = src.replace(b, "pcie_mhi_data != 38u && pcie_mhi_data != 39u) wr(pcie_dma_extra + 20 * 0x2c")

i = src.index(END)
src = src[:i] + BLOCK + src[i:]
assert src.count("apply-419 i:") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-419 ok")
