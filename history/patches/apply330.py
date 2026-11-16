import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
if "pcie_gen" not in s:
    a = "static uint32_t pcie_bw_db = 1, pcie_bw_rp = 1;\t/* apply-328: split the bw ack steps */"
    assert s.count(a) == 1, s.count(a)
    s = s.replace(a, a + "\nstatic uint32_t pcie_gen = 1;\t/* apply-330: target link speed, 1 = gen1, 2 = gen2 */")
old = """	wr(dbi.base + 0xa0, (control & ~0xfu) | 1u);
	wr(dbi.base + 0x80, link & ~3u);"""
new = """	{
		uint32_t g = pcie_gen;

		if (PE_parse_boot_argn("pcie_gen", &g, sizeof(g))) {
			pcie_gen = g;
		}
	}
	wr(dbi.base + 0xa0, (control & ~0xfu) | (pcie_gen & 0xfu));
	wr(dbi.base + 0x80, link & ~3u);
	if (pcie_gen > 1u) {
		/* ask the link to retrain at the new target speed */
		sleep_ms(10);
		wr(dbi.base + 0x80, (link & ~3u) | (1u << 5));
		sleep_ms(20);
		printf("pcie: 4:   apply-330 retrained for gen %u: 0x80 = 0x%08x\\n",
		    pcie_gen, rd(dbi.base + 0x80));
	}
	printf("pcie: 4:   apply-330 gen %u: 0xa0 0x%08x -> 0x%08x\\n",
	    pcie_gen, control, rd(dbi.base + 0xa0));"""
assert s.count(old) == 1
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-330 added")