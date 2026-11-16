#!/usr/bin/env python3
"""apply-429: event ring "empty" convention - wp starts at the LAST element.

Copied from the OnePlus 9 driver (lemonade_wifi.c, mhi_ready()):

    events[i].read  = base;
    events[i].write = base + (mhi_ring_count[i] - 1) * 16;
    mhi.returned[i] = mhi_ring_count[i] - 1;
    ...
    for (i...) mhi_write_address(mhi.event_db + i * 8, events[i].write);

and after consuming an event:

    wr(context + 36, base + mhi.returned[n] * 16);   /* 36 == 0x24 == wp */
    mhi_write_address(mhi.event_db + n * 8, base + mhi.returned[n] * 16);

So on an empty event ring the host-side write pointer sits on the *last* element,
not on element 0.  We have always left it at element 0, which makes the ring look
full from the firmware's side.  Set it the way the working driver does, tell the
device, then try one TRE on ch20.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-429: the empty-ring convention the working driver uses: wp = last element. */
	if (pcie_mhi_data == 49u && smmu_state == 1 && pcie_dma_extra != 0 &&
	    rd(bar0.base + 0x128) == 2u) {
		uint32_t e429, c429, len429, base429, wp429, rp429, k429;
		vm_offset_t ctx429, tre429, buf429;

		sleep_ms(1500);
		/* 1. rewrite the three event ring contexts the vendor way */
		for (e429 = 0; e429 < 3u; e429++) {
			ctx429 = pcie_dma_extra + 0x2000u + e429 * 0x2cu;
			base429 = rd(ctx429 + 0x0cu);
			len429 = rd(ctx429 + 0x14u);
			if (base429 == 0u || len429 == 0u)
				continue;
			wp429 = base429 + len429 - 16u;
			wr(ctx429 + 0x1cu, base429);		/* rp  = first element */
			wr(ctx429 + 0x24u, wp429);		/* wp  = last element  */
			__asm__ __volatile__("dsb sy" ::: "memory");
			wr(bar0.base + 0x700u + e429 * 8u + 4u, 0u);
			wr(bar0.base + 0x700u + e429 * 8u, wp429);
			printf("apply-429 a er%u: rbase 0x%08x len 0x%08x rp 0x%08x wp 0x%08x rung\n",
			    e429, base429, len429, base429, wp429);
		}

		/* 2. one TRE on ch20, doorbell only */
		c429 = 20u * 0x2cu;
		buf429 = pcie_dma_extra + 0x3a0000u;
		for (k429 = 0; k429 < 8u; k429++)
			wr(buf429 + k429 * 4u, 0x5154524bu + k429);
		__asm__ __volatile__("dc civac, %0" :: "r"(buf429) : "memory");
		rp429 = rd(pcie_dma_extra + c429 + 0x1cu);
		wp429 = rd(pcie_dma_extra + c429 + 0x24u);
		tre429 = pcie_dma_extra + (wp429 - (uint32_t)PCIE_EXTRA_IOVA);
		wr(tre429 + 0x00u, (uint32_t)(PCIE_EXTRA_IOVA + 0x3a0000u));
		wr(tre429 + 0x04u, 0u);
		wr(tre429 + 0x08u, 0x00000020u);
		wr(tre429 + 0x0cu, 0x00020000u);
		__asm__ __volatile__("dc civac, %0" :: "r"(tre429) : "memory");
		__asm__ __volatile__("dsb sy" ::: "memory");
		wr(pcie_dma_extra + c429 + 0x24u, wp429 + 0x10u);
		wr(bar0.base + 0x300u + 20u * 8u + 4u, 0u);
		wr(bar0.base + 0x300u + 20u * 8u, wp429 + 0x10u);
		printf("apply-429 b ch20: st 0x%08x tre 0x%llx rung 0x3a0 <- 0x%08x\n",
		    rd(pcie_dma_extra + c429), (unsigned long long)tre429, wp429 + 0x10u);

		/* 3. watch: event ring rp (device producer) plus channel state */
		for (k429 = 0; k429 < 300u; k429++) {
			sleep_ms(10);
			if (!((k429 + 1u) % 30u))
				printf("apply-429 c t=%u ms: ch20 st 0x%08x rp 0x%08x | er0 rp 0x%08x | er1 rp 0x%08x | ee 0x%08x mh 0x%08x\n",
				    (k429 + 1u) * 10u, rd(pcie_dma_extra + c429),
				    rd(pcie_dma_extra + c429 + 0x1cu),
				    rd(pcie_dma_extra + 0x2000u + 0x1cu), rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x1cu),
				    rd(bar0.base + 0x128), rd(bar0.base + 0x48));
			if (rd(pcie_dma_extra + c429) != 0x00000202u)
				break;
		}
		printf("apply-429 d end: ch20 st 0x%08x rp 0x%08x wp 0x%08x er1 rp 0x%08x wp 0x%08x payload %08x\n",
		    rd(pcie_dma_extra + c429), rd(pcie_dma_extra + c429 + 0x1cu), rd(pcie_dma_extra + c429 + 0x24u),
		    rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x1cu), rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x24u),
		    rd(buf429));
		printf("apply-429 done\n");
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1 and "apply-429" not in src

a1 = "pcie_mhi_data != 48u && pcie_chanstart != 0"
a2 = "pcie_mhi_data != 48u) wr(pcie_dma_extra + 20 * 0x2c"
assert src.count(a1) == 1, "gate A"
assert src.count(a2) == 1, "gate B"
src = src.replace(a1, "pcie_mhi_data != 48u && pcie_mhi_data != 49u && pcie_chanstart != 0")
src = src.replace(a2, "pcie_mhi_data != 48u && pcie_mhi_data != 49u) wr(pcie_dma_extra + 20 * 0x2c")

a = src.index(END)
src = src[:a] + BLOCK + src[a:]
assert src.count("apply-429 done") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-429 ok")
