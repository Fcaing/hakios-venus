import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
old = """\t\t\t\t\tfor (w = 0; w < 3000; w += 100) {
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
"""
assert s.count(old) == 1, s.count(old)
new = """\t\t\t\t\tfor (w = 0; w < 600; w += 20) {
\t\t\t\t\t\tuint32_t ee2 = rd(bar0.base + 0x128);
\t\t\t\t\t\tuint32_t mh2 = rd(bar0.base + 0x48);

\t\t\t\t\t\tif (ee2 != last_ee || mh2 != last_mh) {
\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-255 t=%u ee 0x%08x -> 0x%08x mh 0x%08x -> 0x%08x ctrl 0x%08x err 0x%08x fsr 0x%08x gfsr 0x%08x far 0x%08x:%08x\\n",
\t\t\t\t\t\t\t    w, last_ee, ee2, last_mh, mh2,
\t\t\t\t\t\t\t    rd(bar0.base + 0x38), rd(bar0.base + 0x130),
\t\t\t\t\t\t\t    rd(smmu_cb + 0x58), rd(smmu_mmio + 0x48),
\t\t\t\t\t\t\t    rd(smmu_cb + 0x64), rd(smmu_cb + 0x60));
\t\t\t\t\t\t\tlast_ee = ee2;
\t\t\t\t\t\t\tlast_mh = mh2;
\t\t\t\t\t\t}
\t\t\t\t\t\tsleep_ms(20);
\t\t\t\t\t}
"""
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-255 done", len(s))