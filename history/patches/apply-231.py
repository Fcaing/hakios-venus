import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

def sub1(old, new):
    assert s.count(old) == 1, "not unique: %r" % old[:60]
    return s.replace(old, new, 1)

anchor = '''	printf("pcie: 1: every register of the always-on part has been read\\n");
}'''
assert s.count(anchor) == 1

new = '''	printf("pcie: 1: every register of the always-on part has been read\\n");

	{
		uint32_t halt = 0;
		if (PE_parse_boot_argn("pcie_star_halt", &halt, sizeof(halt)) && halt != 0) {
			/*
			 * star's power_root() refuses to touch a root complex it did not power up
			 * itself: its first act is to require cfg_ahb halted (CBCR bit 31 set).
			 * Ours is clocked by ABL, so before anything can be replayed we have to
			 * see whether clearing the votes returns the branch to halted. If it
			 * does not, star's sequence cannot be replayed on this machine at all.
			 */
			uint32_t cfg_before = rd(gcc.base + GCC_CBCR_CFG_AHB);
			uint32_t v1_before = rd(gcc.base + GCC_VOTE_1);
			uint32_t v0_before = rd(gcc.base + GCC_VOTE_0);
			printf("pcie: 1: apply-231: halt experiment, cfg_ahb 0x%08x vote1 0x%08x vote0 0x%08x\\n",
			    cfg_before, v1_before, v0_before);
			sleep_ms(PCIE_SETTLE_MS);

			wr(gcc.base + GCC_VOTE_1, v1_before & ~VOTE_1_MASK);
			wr(gcc.base + GCC_VOTE_0, v0_before & ~VOTE_0_MASK);
			printf("pcie: 1: apply-231: votes cleared to 0x%08x / 0x%08x\\n",
			    rd(gcc.base + GCC_VOTE_1), rd(gcc.base + GCC_VOTE_0));

			uint32_t cfg = cfg_before, gdscr = rd(gcc.base + GCC_GDSCR);
			for (uint32_t i = 0; i < 100; i++) {
				cfg = rd(gcc.base + GCC_CBCR_CFG_AHB);
				gdscr = rd(gcc.base + GCC_GDSCR);
				if ((cfg & CBCR_OFF) && !(gdscr & GDSC_PWR_ON)) {
					break;
				}
				sleep_ms(1);
			}
			printf("pcie: 1: apply-231: after %u ms cfg_ahb 0x%08x (halted %u) gdscr 0x%08x (on %u)\\n",
			    0u, cfg, (cfg & CBCR_OFF) >> 31, gdscr, (gdscr & GDSC_PWR_ON) >> 31);
			sleep_ms(PCIE_SETTLE_MS);

			/* put everything back the way it was, whatever the outcome */
			wr(gcc.base + GCC_VOTE_1, v1_before);
			wr(gcc.base + GCC_VOTE_0, v0_before);
			sleep_ms(50);
			printf("pcie: 1: apply-231: restored cfg_ahb 0x%08x vote1 0x%08x vote0 0x%08x\\n",
			    rd(gcc.base + GCC_CBCR_CFG_AHB), rd(gcc.base + GCC_VOTE_1),
			    rd(gcc.base + GCC_VOTE_0));
		}
	}
}'''
s = sub1(anchor, new)
io.open(p, "w", encoding="utf-8").write(s)
print("ok apply-231")