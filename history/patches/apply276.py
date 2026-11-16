import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
n0 = len(s)

a = "static uint32_t pcie_mhi_watch;\t/* apply-271: watch the rings for a while after amss is up */"
assert s.count(a) == 1
s = s.replace(a, a + "\nstatic uint32_t pcie_mhi_earlym0;\t/* apply-276: ask for m0 right after bhi, like the vendor does */")

a2 = """\t\t\t\t\t\t\twant2 = 0;
\t\t\t\t\t\t\tif (PE_parse_boot_argn("pcie_mhi_watch", &want2, sizeof(want2))) {
\t\t\t\t\t\t\t\tpcie_mhi_watch = want2;
\t\t\t\t\t\t\t}"""
assert s.count(a2) == 1
s = s.replace(a2, a2 + """
\t\t\t\t\t\t\twant2 = 0;
\t\t\t\t\t\t\tif (PE_parse_boot_argn("pcie_mhi_earlym0", &want2, sizeof(want2))) {
\t\t\t\t\t\t\t\tpcie_mhi_earlym0 = want2;
\t\t\t\t\t\t\t}""")

a3 = """\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-264 before init: mh 0x%08x ee 0x%08x cfg 0x%08x ctrl 0x%08x\\n","""
assert s.count(a3) == 1
s = s.replace(a3, """\t\t\t\t\t\t\t/* apply-276: the vendor asks for m0 inside the same
\t\t\t\t\t\t\t * millisecond that READY goes up; ask now, before the
\t\t\t\t\t\t\t * contexts are touched. */
\t\t\t\t\t\t\tif (pcie_mhi_earlym0 != 0) {
\t\t\t\t\t\t\t\twr(bar0.base + 0x38,
\t\t\t\t\t\t\t\t    (rd(bar0.base + 0x38) & ~0xff00u) | (2u << 8));
\t\t\t\t\t\t\t\tsleep_ms(2);
\t\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-276 early m0: mh 0x%08x ee 0x%08x ctrl 0x%08x\\n",
\t\t\t\t\t\t\t\t    rd(bar0.base + 0x48), rd(bar0.base + 0x128),
\t\t\t\t\t\t\t\t    rd(bar0.base + 0x38));
\t\t\t\t\t\t\t}

""" + a3)

io.open(p, "w", encoding="utf-8").write(s)
print("ok", n0, "->", len(s))