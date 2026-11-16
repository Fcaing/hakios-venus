import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
anchor = '\t\t\tprintf("pcie: 5:   pcie_bar=%u: pave first, then move the bar\\n",\n\t\t\t       pcie_bar);\n'
assert s.count(anchor) == 1
add = anchor + """
\t\t\t/* apply-174: bar0 is decoded by the memory window that dbi 0x20 names,
\t\t\t * and the endpoint's BAR0 has to be given that address first.  Without
\t\t\t * both, every read through bar0 comes back 0xffffffff (p175). */
\t\t\tif (pcie_bar == 21 || pcie_bar == 22 || pcie_bar == 23) {
\t\t\t\twr(dbi.base + 0x20, 0x60506040);
\t\t\t\twr(conf.base + 0x10, 0x60400004);
\t\t\t\tprintf("pcie: 5:   bar0 window: dbi 0x20 = 0x%08x, BAR0 = 0x%08x\\n",
\t\t\t\t       rd(dbi.base + 0x20), rd(conf.base + 0x10));
\t\t\t}
"""
s = s.replace(anchor, add, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-174 applied")
