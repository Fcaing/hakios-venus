import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
n0 = len(s)

a = """\t\t\t\t\t\t\tif (pcie_mhi_nom0 == 0) {
\t\t\t\t\t\t\t\twr(bar0.base + 0x38, (rd(bar0.base + 0x38) & ~0xff00u) | (2u << 8));"""
assert s.count(a) == 1
s = s.replace(a, """\t\t\t\t\t\t\tif (pcie_mhi_nom0 == 0) {
\t\t\t\t\t\t\t\tif (smmu_state == 1) {
\t\t\t\t\t\t\t\t\twr(smmu_cb + 0x58, PCIE_SMMU_FAULT);
\t\t\t\t\t\t\t\t\twr(smmu_mmio + 0x48, PCIE_SMMU_FAULT);
\t\t\t\t\t\t\t\t\t__asm__ volatile ("dsb sy" : : : "memory");
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\twr(bar0.base + 0x38, (rd(bar0.base + 0x38) & ~0xff00u) | (2u << 8));
\t\t\t\t\t\t\t\tif (smmu_state == 1) {
\t\t\t\t\t\t\t\t\tsleep_ms(20);
\t\t\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-273 m0 fault check: fsr 0x%08x far 0x%08x:%08x gfsr 0x%08x mh 0x%08x ee 0x%08x\\n",
\t\t\t\t\t\t\t\t\t    rd(smmu_cb + 0x58), rd(smmu_cb + 0x64), rd(smmu_cb + 0x60),
\t\t\t\t\t\t\t\t\t    rd(smmu_mmio + 0x48), rd(bar0.base + 0x48), rd(bar0.base + 0x128));
\t\t\t\t\t\t\t\t}""")

io.open(p, "w", encoding="utf-8").write(s)
print("ok", n0, "->", len(s))