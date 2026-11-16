import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
n0 = len(s)

a = "static uint32_t pcie_mhi_nobase;\t/* apply-267: leave the mhi base/limit registers alone */"
assert s.count(a) == 1
s = s.replace(a, a + "\nstatic uint32_t pcie_mhi_nom0;\t/* apply-270: do not ask for m0, let the device do it */")

a2 = """\t\t\t\t\t\t\tPE_parse_boot_argn("pcie_mhi_nobase", &want2, sizeof(want2));
\t\t\t\t\t\t\tpcie_mhi_nobase = want2;"""
assert s.count(a2) == 1
s = s.replace(a2, a2 + """
\t\t\t\t\t\t\tPE_parse_boot_argn("pcie_mhi_nom0", &want2, sizeof(want2));
\t\t\t\t\t\t\tpcie_mhi_nom0 = want2;""")

a3 = "\t\t\t\t\t\t\twr(bar0.base + 0x38, (rd(bar0.base + 0x38) & ~0xff00u) | (2u << 8));"
assert s.count(a3) == 1
s = s.replace(a3, """\t\t\t\t\t\t\tif (pcie_mhi_nom0 == 0) {
\t\t\t\t\t\t\t\twr(bar0.base + 0x38, (rd(bar0.base + 0x38) & ~0xff00u) | (2u << 8));
\t\t\t\t\t\t\t} else {
\t\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-270 m0 skipped, mh 0x%08x ctrl 0x%08x\\n",
\t\t\t\t\t\t\t\t    rd(bar0.base + 0x48), rd(bar0.base + 0x38));
\t\t\t\t\t\t\t}""")

io.open(p, "w", encoding="utf-8").write(s)
print("ok", n0, "->", len(s))