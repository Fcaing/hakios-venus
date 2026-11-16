import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

a1 = "\t\t\t\t\t\t\twr(bar0.base + 0x5c, (uint32_t)(ctxt >> 32));\n"
assert s.count(a1) == 1
s = s.replace(a1, """\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-264 before init: mh 0x%08x ee 0x%08x cfg 0x%08x ctrl 0x%08x\\n",
\t\t\t\t\t\t\t    rd(bar0.base + 0x48), rd(bar0.base + 0x128),
\t\t\t\t\t\t\t    rd(bar0.base + 0x10), rd(bar0.base + 0x38));
""" + a1)

a2 = "\t\t\t\t\t\t\twr(bar0.base + 0x10, 0x00030880u);\n"
assert s.count(a2) == 1
s = s.replace(a2, """\t\t\t\t\t\t\t{
\t\t\t\t\t\t\t\tuint32_t nocfg = 0;
\t\t\t\t\t\t\t\tPE_parse_boot_argn("pcie_mhi_nocfg", &nocfg, sizeof(nocfg));
\t\t\t\t\t\t\t\tif (nocfg == 0) {
\t\t\t\t\t\t\t\t\twr(bar0.base + 0x10, 0x00030880u);
\t\t\t\t\t\t\t\t} else {
\t\t\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-264 mhicfg left alone, reads 0x%08x\\n", rd(bar0.base + 0x10));
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t}
""")

a3 = "\t\t\t\t\t\t\twr(bar0.base + 0x38, (rd(bar0.base + 0x38) & ~0xff00u) | (2u << 8));\n"
assert s.count(a3) == 1
s = s.replace(a3, a3 + """\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-264 after m0: mh 0x%08x ee 0x%08x ctrl 0x%08x\\n",
\t\t\t\t\t\t\t    rd(bar0.base + 0x48), rd(bar0.base + 0x128), rd(bar0.base + 0x38));
""")
io.open(p, "w", encoding="utf-8").write(s)
print("apply-264 inserted")