import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
old = "static uint32_t pcie_trap;"
assert s.count(old) == 1
s = s.replace(old, old + "\nstatic uint32_t pcie_mhi_state_val = 2;\t/* apply-314: which MHISTATE to request after bhie */")
old2 = """								d2 = 0;
								if (PE_parse_boot_argn("pcie_trap", &d2, sizeof(d2))) {
									pcie_trap = d2;
								}"""
assert s.count(old2) == 1
s = s.replace(old2, old2 + """
								d2 = 0;
								if (PE_parse_boot_argn("pcie_mhi_state_val", &d2, sizeof(d2))) {
									pcie_mhi_state_val = d2;
								}""")
old3 = "wr(bar0.base + 0x38, (m0old &\t~0xff00u) | (2u << 8));"
if s.count(old3) != 1:
    import re
    m = re.search(r"wr\(bar0\.base \+ 0x38, \(m0old &[^\n]*2u << 8\)\);", s)
    assert m, "no m0 write found"
    old3 = m.group(0)
s = s.replace(old3, "wr(bar0.base + 0x38, (m0old & ~0xff00u) | (pcie_mhi_state_val << 8));")
io.open(p, "w", encoding="utf-8").write(s)
print("apply-314 written")