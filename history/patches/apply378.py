P = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(P).read()

start_marker = "\t/*\n\t * apply-377:"
end_marker = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

a = s.index(start_marker)
b = s.index(end_marker)
assert a < b, (a, b)
assert s.count(end_marker) == 1

new = r'''	/*
	 * apply-378: p418 wrote 0xb0 (MHI_SOC_RESET_REQ) for the first time and got the
	 * only state change this tree has ever bought with a register write: ee 2 -> 3
	 * (rddm) inside 20 ms, and back to 2 within half a second.  Question one is what
	 * happens in between -- a real reset walking through sbl, or a transient the
	 * firmware takes back.  Question two is the one m8 needs: does the firmware's mhi
	 * client come back up able to service the command ring it has ignored for sixteen
	 * rounds.  So: a 1 ms timeline, then re-ring 0x70 and the channel doorbells and
	 * watch rp move -- or sit there.
	 */
	if (pcie_socreset != 0 && smmu_state == 1) {
		uint32_t t, k, moved, nevt = 0, nevt2 = 0, changes = 0;
		uint32_t lastee = 0xffffffffu, lastmh = 0xffffffffu;
		uint32_t t_rddm = 0, t_back = 0, rp, wp;
		uint32_t ch20 = 0x2000u + 20u * 0x2c, ch21 = 0x2000u + 21u * 0x2c, cmd = 0x2400u;

		if (pcie_dma_extra != 0) {
			__asm__ volatile ("dc ivac, %0" : : "r" (pcie_dma_extra + 0x2000) : "memory");
			__asm__ volatile ("dsb sy" : : : "memory");
			while (nevt < 0x40 &&
			    (rd(pcie_dma_extra + 0x4000 + nevt * 0x10 + 0x8) != 0 ||
			     rd(pcie_dma_extra + 0x4000 + nevt * 0x10 + 0xc) != 0)) {
				nevt++;
			}
		}
		printf("pcie: 5:   21: apply-378 t0: ee 0x%08x mh 0x%08x ctrl 0x%08x b0 0x%08x evts %u "
		    "ch20 st 0x%08x rp 0x%08x wp 0x%08x er0 rp 0x%08x wp 0x%08x cmd rp 0x%08x wp 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(bar0.base + 0x38), rd(bar0.base + 0xb0),
		    (unsigned)nevt, rd(pcie_dma_extra + ch20), rd(pcie_dma_extra + ch20 + 0x1c),
		    rd(pcie_dma_extra + ch20 + 0x24), rd(pcie_dma_extra + 0x201c),
		    rd(pcie_dma_extra + 0x2024), rd(pcie_dma_extra + cmd + 0x1c),
		    rd(pcie_dma_extra + cmd + 0x24));

		wr(bar0.base + 0xb0, 1u);
		printf("pcie: 5:   21: apply-378 b0 got 1: b0 0x%08x ee 0x%08x mh 0x%08x\n",
		    rd(bar0.base + 0xb0), rd(bar0.base + 0x128), rd(bar0.base + 0x48));

		for (t = 1; t <= 3000; t++) {
			uint32_t ee = rd(bar0.base + 0x128);
			uint32_t mh = rd(bar0.base + 0x48);

			if (ee != lastee || mh != lastmh) {
				if (ee == 3u && t_rddm == 0) {
					t_rddm = t;
				}
				if (t_rddm != 0 && ee == 2u && t_back == 0) {
					t_back = t;
				}
				printf("pcie: 5:   21: apply-378 t=%u ms: ee 0x%08x mh 0x%08x ctrl 0x%08x b0 0x%08x\n",
				    t, ee, mh, rd(bar0.base + 0x38), rd(bar0.base + 0xb0));
				lastee = ee;
				lastmh = mh;
				changes++;
			}
			sleep_ms(1);
		}
		printf("pcie: 5:   21: apply-378 timeline: changes %u t_rddm %u ms t_back %u ms "
		    "end ee 0x%08x mh 0x%08x\n", changes, t_rddm, t_back,
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48));

		if (pcie_dma_extra != 0) {
			printf("pcie: 5:   21: apply-378 after reset ch20 st 0x%08x rp 0x%08x wp 0x%08x "
			    "ch21 st 0x%08x rp 0x%08x er0 rp 0x%08x wp 0x%08x\n",
			    rd(pcie_dma_extra + ch20), rd(pcie_dma_extra + ch20 + 0x1c),
			    rd(pcie_dma_extra + ch20 + 0x24), rd(pcie_dma_extra + ch21),
			    rd(pcie_dma_extra + ch21 + 0x1c), rd(pcie_dma_extra + 0x201c),
			    rd(pcie_dma_extra + 0x2024));

			/* 1. the command ring: four TREs are still queued there and rp never moved. */
			rp = rd(pcie_dma_extra + cmd + 0x1c);
			wp = rd(pcie_dma_extra + cmd + 0x24);
			wr(bar0.base + 0x70, wp);
			printf("pcie: 5:   21: apply-378 cmd redrive: db 0x%08x rp before 0x%08x\n", wp, rp);
			moved = 0;
			for (k = 1; k <= 60; k++) {
				uint32_t now;

				__asm__ volatile ("dc ivac, %0" : : "r" (pcie_dma_extra + cmd + 0x1c) : "memory");
				__asm__ volatile ("dsb sy" : : : "memory");
				now = rd(pcie_dma_extra + cmd + 0x1c);
				if (now != rp) {
					printf("pcie: 5:   21: apply-378 cmd rp moved to 0x%08x after %u ms\n",
					    now, k * 5u);
					moved = 1;
					break;
				}
				sleep_ms(5);
			}
			if (moved == 0) {
				printf("pcie: 5:   21: apply-378 cmd rp did not move in 300 ms\n");
			}

			/* 2. the data channel: same doorbell the vendor rings, same value. */
			wp = rd(pcie_dma_extra + ch20 + 0x24);
			rp = rd(pcie_dma_extra + ch20 + 0x1c);
			wr(bar0.base + 0x300 + 20 * 8 + 4, 0u);
			wr(bar0.base + 0x300 + 20 * 8, wp);
			printf("pcie: 5:   21: apply-378 ch20 redrive: db 0x%08x rp before 0x%08x\n", wp, rp);
			moved = 0;
			for (k = 1; k <= 60; k++) {
				uint32_t now;

				__asm__ volatile ("dc ivac, %0" : : "r" (pcie_dma_extra + ch20 + 0x1c) : "memory");
				__asm__ volatile ("dsb sy" : : : "memory");
				now = rd(pcie_dma_extra + ch20 + 0x1c);
				if (now != rp) {
					printf("pcie: 5:   21: apply-378 ch20 rp moved to 0x%08x after %u ms\n",
					    now, k * 5u);
					moved = 1;
					break;
				}
				sleep_ms(5);
			}
			if (moved == 0) {
				printf("pcie: 5:   21: apply-378 ch20 rp did not move in 300 ms\n");
			}

			/* 3. did rddm leave anything new on the event ring? */
			__asm__ volatile ("dc ivac, %0" : : "r" (pcie_dma_extra + 0x4000) : "memory");
			__asm__ volatile ("dsb sy" : : : "memory");
			while (nevt2 < 0x40 &&
			    (rd(pcie_dma_extra + 0x4000 + nevt2 * 0x10 + 0x8) != 0 ||
			     rd(pcie_dma_extra + 0x4000 + nevt2 * 0x10 + 0xc) != 0)) {
				nevt2++;
			}
			printf("pcie: 5:   21: apply-378 end: evts %u end ee 0x%08x mh 0x%08x "
			    "er[0] %08x %08x %08x %08x | er[4] %08x %08x %08x %08x\n",
			    (unsigned)nevt2, rd(bar0.base + 0x128), rd(bar0.base + 0x48),
			    rd(pcie_dma_extra + 0x4000 + 0x0), rd(pcie_dma_extra + 0x4010 + 0x0),
			    rd(pcie_dma_extra + 0x4020 + 0x0), rd(pcie_dma_extra + 0x4030 + 0x0),
			    rd(pcie_dma_extra + 0x4040 + 0x0), rd(pcie_dma_extra + 0x4050 + 0x0),
			    rd(pcie_dma_extra + 0x4060 + 0x0), rd(pcie_dma_extra + 0x4070 + 0x0));
		}
	}

'''

s = s[:a] + new + s[b:]
open(P, "w").write(s)
print("apply-378 ok")
