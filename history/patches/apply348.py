import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
old = """	{
		uint32_t rt = pcie_retrain;

		if (PE_parse_boot_argn("pcie_retrain", &rt, sizeof(rt))) {
			pcie_retrain = rt;
		}
	}
	if (pcie_gen > 1u && pcie_retrain != 0) {
"""
new = """	if (pcie_gen > 1u) {		/* apply-348: back to the unconditional poke the good kernel had */
"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-348 ok")