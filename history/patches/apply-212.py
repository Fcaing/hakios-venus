import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old = """\t\t\t\t\tif (smmu_state == 1) {
\t\t\t\t\t\tprintf("pcie: 5:   21: fsr before doorbell 0x%08x gfsr 0x%08x far 0x%08x:%08x\\n",
\t\t\t\t\t\t    rd(smmu_cb + 0x58), rd(smmu_mmio + 0x48),
\t\t\t\t\t\t    rd(smmu_cb + 0x64), rd(smmu_cb + 0x60));
\t\t\t\t\t}"""
assert s.count(old) == 1, s.count(old)
new = """\t\t\t\t\tif (smmu_state == 1) {
\t\t\t\t\t\tuint64_t *pt1 = (uint64_t *)smmu_tables;
\t\t\t\t\t\tuint64_t *pt2 = (uint64_t *)(smmu_tables + PAGE_SIZE);
\t\t\t\t\t\tuint64_t *pt3 = (uint64_t *)(smmu_tables + 2 * PAGE_SIZE);

\t\t\t\t\t\tprintf("pcie: 5:   21: fsr before doorbell 0x%08x gfsr 0x%08x far 0x%08x:%08x\\n",
\t\t\t\t\t\t    rd(smmu_cb + 0x58), rd(smmu_mmio + 0x48),
\t\t\t\t\t\t    rd(smmu_cb + 0x64), rd(smmu_cb + 0x60));
\t\t\t\t\t\tprintf("pcie: 5:   21: pt l1[2] 0x%016llx l2[256] 0x%016llx l3[4] 0x%016llx dma kvtophys 0x%llx\\n",
\t\t\t\t\t\t    (unsigned long long)pt1[2], (unsigned long long)pt2[256],
\t\t\t\t\t\t    (unsigned long long)pt3[4],
\t\t\t\t\t\t    (unsigned long long)kvtophys(pcie_dma));
\t\t\t\t\t\tprintf("pcie: 5:   21: cbar 0x%08x cba2r 0x%08x tcr 0x%08x sctlr 0x%08x\\n",
\t\t\t\t\t\t    rd(smmu_mmio + 0x1000 + 4 * smmu_context),
\t\t\t\t\t\t    rd(smmu_mmio + 0x1800 + 4 * smmu_context),
\t\t\t\t\t\t    rd(smmu_cb + 0x30), rd(smmu_cb + 0x10));
\t\t\t\t\t}"""
s = s.replace(old, new, 1)

old2 = """\t\t\t\tif (smmu_state == 1) {
\t\t\t\t\tprintf("pcie: 5:   21: fsr after doorbell 0x%08x gfsr 0x%08x far 0x%08x:%08x\\n",
\t\t\t\t\t    rd(smmu_cb + 0x58), rd(smmu_mmio + 0x48),
\t\t\t\t\t    rd(smmu_cb + 0x64), rd(smmu_cb + 0x60));
\t\t\t\t}"""
assert s.count(old2) == 1, s.count(old2)
new2 = """\t\t\t\tif (smmu_state == 1) {
\t\t\t\t\tuint64_t *pt1 = (uint64_t *)smmu_tables;
\t\t\t\t\tuint64_t *pt2 = (uint64_t *)(smmu_tables + PAGE_SIZE);
\t\t\t\t\tuint64_t *pt3 = (uint64_t *)(smmu_tables + 2 * PAGE_SIZE);

\t\t\t\t\tprintf("pcie: 5:   21: fsr after doorbell 0x%08x gfsr 0x%08x far 0x%08x:%08x\\n",
\t\t\t\t\t    rd(smmu_cb + 0x58), rd(smmu_mmio + 0x48),
\t\t\t\t\t    rd(smmu_cb + 0x64), rd(smmu_cb + 0x60));
\t\t\t\t\tprintf("pcie: 5:   21: pt after l1[2] 0x%016llx l2[256] 0x%016llx l3[4] 0x%016llx\\n",
\t\t\t\t\t    (unsigned long long)pt1[2], (unsigned long long)pt2[256],
\t\t\t\t\t    (unsigned long long)pt3[4]);
\t\t\t\t}"""
s = s.replace(old2, new2, 1)

io.open(p, "w", encoding="utf-8").write(s)
print("ok apply-212")