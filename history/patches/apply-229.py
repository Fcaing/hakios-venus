import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

def sub1(old, new):
    assert s.count(old) == 1, "not unique: %r" % old[:60]
    return s.replace(old, new, 1)

anchor = 'wr(bar0.base + 0x118, db);'
assert s.count(anchor) >= 1

probe = '''	{
		uint32_t m0 = 0;
		if (PE_parse_boot_argn("pcie_m0_early", &m0, sizeof(m0)) && m0 != 0) {
			uint32_t ctrl = rd(bar0.base + 0x38);
			wr(bar0.base + 0x38, (ctrl & ~0xff00u) | (2u << 8));
			printf("pcie: 5:   21: apply-229: mhictrl 0x%08x -> 0x%08x (M0 early)\\n",
			    ctrl, rd(bar0.base + 0x38));
		}
	}

'''

s = sub1(anchor, probe + anchor)
io.open(p, "w", encoding="utf-8").write(s)
print("ok m0 early")