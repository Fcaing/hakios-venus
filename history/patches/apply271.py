import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
n0 = len(s)

a = "static uint32_t pcie_mhi_nom0;\t/* apply-270: do not ask for m0, let the device do it */"
assert s.count(a) == 1
s = s.replace(a, a + "\nstatic uint32_t pcie_mhi_watch;\t/* apply-271: watch the rings for a while after amss is up */")

a2 = """\t\t\t\t\t\t\tPE_parse_boot_argn("pcie_mhi_nom0", &want2, sizeof(want2));
\t\t\t\t\t\t\tpcie_mhi_nom0 = want2;"""
assert s.count(a2) == 1
s = s.replace(a2, a2 + """
\t\t\t\t\t\t\tPE_parse_boot_argn("pcie_mhi_watch", &want2, sizeof(want2));
\t\t\t\t\t\t\tpcie_mhi_watch = want2;""")

a3 = """\t\t\t\t\tprintf("pcie: 5:   21: apply-252 done ee 0x%08x mh 0x%08x ctrl 0x%08x err 0x%08x\\n",
\t\t\t\t\t    last_ee, last_mh, rd(bar0.base + 0x38), rd(bar0.base + 0x130));"""
assert s.count(a3) == 1
s = s.replace(a3, a3 + """
\t\t\t\t\tif (pcie_mhi_watch != 0 && smmu_state == 1) {
\t\t\t\t\t\tunsigned w;

\t\t\t\t\t\tfor (w = 0; w < pcie_mhi_watch; w++) {
\t\t\t\t\t\t\tuint32_t f0, f1, f2, g0, g1, g2;

\t\t\t\t\t\t\tsleep_ms(1000);
\t\t\t\t\t\t\tf0 = rd(bar0.base + 0x228);
\t\t\t\t\t\t\tf1 = rd(bar0.base + 0x328);
\t\t\t\t\t\t\tf2 = rd(bar0.base + 0x428);
\t\t\t\t\t\t\tg0 = rd(bar0.base + 0x230);
\t\t\t\t\t\t\tg1 = rd(bar0.base + 0x330);
\t\t\t\t\t\t\tg2 = rd(bar0.base + 0x430);
\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-271 t=%u ee 0x%08x mh 0x%08x ch0 rp 0x%08x wp 0x%08x ch1 wp 0x%08x er0 wp 0x%08x er1 wp 0x%08x er2 wp 0x%08x\\n",
\t\t\t\t\t\t\t    w, rd(bar0.base + 0x128), rd(bar0.base + 0x48),
\t\t\t\t\t\t\t    f0, g0, g1, f1, f2, g2);
\t\t\t\t\t\t}
\t\t\t\t\t}""")

io.open(p, "w", encoding="utf-8").write(s)
print("ok", n0, "->", len(s))