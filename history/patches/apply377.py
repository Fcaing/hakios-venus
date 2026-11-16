P = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(P).read()

a = "static uint32_t pcie_img512;\t/* apply-376"
assert s.count(a) == 1
s = s.replace(a, "static uint32_t pcie_socreset;\t/* apply-377: host requested soc reset through 0xb0 */\n" + a)

b = 'PE_parse_boot_argn("pcie_img512", &pcie_img512, sizeof(pcie_img512));'
assert s.count(b) == 1
s = s.replace(b, b + '\n\tPE_parse_boot_argn("pcie_socreset", &pcie_socreset, sizeof(pcie_socreset));')

c = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"
assert s.count(c) == 1, s.count(c)

block = r'''	/*
	 * apply-377: the one reset path this tree has never touched.  When the
	 * endpoint refuses to answer, the vendor falls back to a host requested
	 * soc reset: mhi_internal.h:132 MHI_SOC_RESET_REQ_OFFSET (0xb0),
	 * MHI_SOC_RESET_REQ = BIT(0), written from mhi_boot.c:214-235 right
	 * after mhi_set_mhi_state(SYS_ERR) fails to take.  Sixteen rounds of
	 * MHICTRL writes did nothing; if 0xb0 really resets the soc, ee has to
	 * fall back to sbl(1) or pbl(0) on its own and the whole handshake can
	 * be replayed inside one round instead of one phone reboot.  If it does
	 * not move, perst# is the only reset left and the vendor path is dead
	 * on this part.
	 */
	if (pcie_socreset != 0 && smmu_state == 1) {
		uint32_t t, nevt = 0;
		uint32_t lastmh = 0xffffffffu;
		uint32_t lastee = 0xffffffffu;

		if (pcie_dma_extra != 0) {
			__asm__ volatile ("dc ivac, %0" : : "r" (pcie_dma_extra + 0x2000) : "memory");
			__asm__ volatile ("dsb sy" : : : "memory");
			while (nevt < 0x40 &&
			    (rd(pcie_dma_extra + 0x4000 + nevt * 0x10 + 0x8) != 0 ||
			     rd(pcie_dma_extra + 0x4000 + nevt * 0x10 + 0xc) != 0)) {
				nevt++;
			}
		}
		printf("pcie: 5:   21: apply-377 t0: mh 0x%08x ee 0x%08x ctrl 0x%08x cfg 0x%08x "
		    "chdb 0x%08x erdb 0x%08x b0 0x%08x bhioff 0x%08x socid 0x%08x evts %u\n",
		    rd(bar0.base + 0x48), rd(bar0.base + 0x128), rd(bar0.base + 0x38),
		    rd(bar0.base + 0x10), rd(bar0.base + 0x18), rd(bar0.base + 0x20),
		    rd(bar0.base + 0xb0), rd(bar0.base + 0x2c), rd(bar0.base + 0x224),
		    (unsigned)nevt);
		wr(bar0.base + 0xb0, 1u);
		printf("pcie: 5:   21: apply-377 b0 got 1: b0 0x%08x mh 0x%08x ee 0x%08x\n",
		    rd(bar0.base + 0xb0), rd(bar0.base + 0x48), rd(bar0.base + 0x128));
		for (t = 1; t <= 400; t++) {
			uint32_t mh = rd(bar0.base + 0x48);
			uint32_t ee = rd(bar0.base + 0x128);

			if (mh != lastmh || ee != lastee) {
				printf("pcie: 5:   21: apply-377 t=%u ms: mh 0x%08x ee 0x%08x "
				    "ctrl 0x%08x cfg 0x%08x b0 0x%08x socid 0x%08x\n",
				    t * 5u, mh, ee, rd(bar0.base + 0x38), rd(bar0.base + 0x10),
				    rd(bar0.base + 0xb0), rd(bar0.base + 0x224));
				lastmh = mh;
				lastee = ee;
			}
			sleep_ms(5);
		}
		printf("pcie: 5:   21: apply-377 end after 2 s: mh 0x%08x ee 0x%08x cfg 0x%08x "
		    "chdb 0x%08x erdb 0x%08x b0 0x%08x socid 0x%08x bhie txstat 0x%08x\n",
		    rd(bar0.base + 0x48), rd(bar0.base + 0x128), rd(bar0.base + 0x10),
		    rd(bar0.base + 0x18), rd(bar0.base + 0x20), rd(bar0.base + 0xb0),
		    rd(bar0.base + 0x224), rd(bar0.base + 0x224 + 0x44));
	}

'''

s = s.replace(c, block + c)
open(P, "w").write(s)
print("apply-377 ok")
