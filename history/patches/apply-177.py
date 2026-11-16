import io

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old = """		if (!(rd(cb) & 1) && !(rd(cb + 0x58) & PCIE_SMMU_FAULT)) {"""
new = """		/*
		 * apply-177: context 0 read back a CBAR of 0x1f000, so the ABL or
		 * Linux had already configured it.  Take a context whose CBAR is
		 * still zero instead of overwriting someone else's translation.
		 */
		if (!(rd(cb) & 1) && !(rd(cb + 0x58) & PCIE_SMMU_FAULT) &&
		    rd(smmu_mmio + 0x1000 + 4 * i) == 0) {"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

old = """				wr(bar0.base + 0x118, 1);
				sleep_ms(100);"""
new = """				wr(bar0.base + 0x118, 1);
				sleep_ms(300);"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

old = """					pcie_note("bhi 0x%08x mhi 0x%08x err 0x%08x; ", st,
					          rd(bar0.base + 0x100), rd(bar0.base + 0x130));
				}"""
new = """					pcie_note("bhi 0x%08x mhi 0x%08x err 0x%08x; ", st,
					          rd(bar0.base + 0x100), rd(bar0.base + 0x130));
					/*
					 * apply-177: if the endpoint did fetch something, the
					 * context bank says so in its FSR/FAR even when PBL
					 * never answers.
					 */
					printf("pcie: 5:   21: smmu after: cb fsr 0x%08x far 0x%08x gfsr 0x%08x scr 0x%08x\\n",
					       rd(smmu_cb + 0x58), rd(smmu_cb + 0x50),
					       rd(smmu_mmio + 0x48), rd(smmu_mmio));
				}"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

io.open(p, "w", encoding="utf-8").write(s)
print("patched")