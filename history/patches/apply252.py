import io
path = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
src = io.open(path, encoding="utf-8").read()
a = "\t\t\t\t\tpcie_note(\"bhie 0x%08x ee 0x%08x; \", st, rd(bar0.base + 0x128));\n\t\t\t\t}\n"
assert src.count(a) == 1, src.count(a)
block = a + """\t\t\t\t/*
\t\t\t\t * apply-252: what does the device do once bhie is accepted?
\t\t\t\t * Watch the execution environment and the mhi state for a few
\t\t\t\t * seconds instead of sampling once.
\t\t\t\t */
\t\t\t\t{
\t\t\t\t\tuint32_t w;
\t\t\t\t\tuint32_t last_ee = rd(bar0.base + 0x128);
\t\t\t\t\tuint32_t last_mh = rd(bar0.base + 0x48);

\t\t\t\t\tprintf("pcie: 5:   21: apply-252 t=0 ee 0x%08x mh 0x%08x ctrl 0x%08x err 0x%08x\\n",
\t\t\t\t\t    last_ee, last_mh, rd(bar0.base + 0x38), rd(bar0.base + 0x130));
\t\t\t\t\tfor (w = 0; w < 3000; w += 100) {
\t\t\t\t\t\tuint32_t ee2 = rd(bar0.base + 0x128);
\t\t\t\t\t\tuint32_t mh2 = rd(bar0.base + 0x48);

\t\t\t\t\t\tif (ee2 != last_ee || mh2 != last_mh) {
\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-252 t=%u ee 0x%08x -> 0x%08x mh 0x%08x -> 0x%08x ctrl 0x%08x err 0x%08x\\n",
\t\t\t\t\t\t\t    w, last_ee, ee2, last_mh, mh2,
\t\t\t\t\t\t\t    rd(bar0.base + 0x38), rd(bar0.base + 0x130));
\t\t\t\t\t\t\tlast_ee = ee2;
\t\t\t\t\t\t\tlast_mh = mh2;
\t\t\t\t\t\t}
\t\t\t\t\t\tsleep_ms(100);
\t\t\t\t\t}
\t\t\t\t\tprintf("pcie: 5:   21: apply-252 done ee 0x%08x mh 0x%08x ctrl 0x%08x err 0x%08x\\n",
\t\t\t\t\t    last_ee, last_mh, rd(bar0.base + 0x38), rd(bar0.base + 0x130));
\t\t\t\t}
"""
src = src.replace(a, block)
io.open(path, "w", encoding="utf-8").write(src)
print("apply-252 done", len(src))