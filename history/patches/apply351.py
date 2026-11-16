import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
old = """							want2 = 0;
							if (PE_parse_boot_argn("pcie_mhi_nom0", &want2, sizeof(want2))) {
							want2 = 0;
							if (PE_parse_boot_argn("pcie_rp_fix", &want2, sizeof(want2))) {
								pcie_rp_fix = want2;
							}
								pcie_mhi_nom0 = want2;
							}
"""
new = """							want2 = 0;
							if (PE_parse_boot_argn("pcie_mhi_nom0", &want2, sizeof(want2))) {
								pcie_mhi_nom0 = want2;	/* apply-351: this nest was mangled, nom0 always read back 0 */
							}
							want2 = 0;
							if (PE_parse_boot_argn("pcie_rp_fix", &want2, sizeof(want2))) {
								pcie_rp_fix = want2;
							}
"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-351 ok")