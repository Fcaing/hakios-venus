import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
n = len(s)
a = """\tfor (page = 0; page < PCIE_DMA_SIZE / 4096; page++) {
\t\tuint64_t pte = l3[((PCIE_SMMU_IOVA + page * 4096) >> 12) & 511];

\t\tif ((pte & 0x0000fffffffff000ull) != kvtophys(pcie_dma + page * 4096)) {"""
assert s.count(a) == 1
s = s.replace(a, """\tfor (page = 0; page < PCIE_DMA_SIZE / 4096; page++) {
\t\tuint64_t pte = l3[((PCIE_SMMU_IOVA + page * 4096) >> 12) & 511];

\t\t/*
\t\t\t * apply-248: with headonly the pages above the limit are
\t\t\t * deliberately unmapped, and walking them made this self
\t\t\t * check fail, which in turn silenced the fsr watcher that
\t\t\t * is the whole point of the experiment.
\t\t\t */
\t\tif (pcie_headonly != 0 &&
\t\t    page >= (pcie_headonly_pages != 0 ? pcie_headonly_pages : 1u)) {
\t\t\tbreak;
\t\t}
\t\tif ((pte & 0x0000fffffffff000ull) != kvtophys(pcie_dma + page * 4096)) {""")
io.open(p, "w", encoding="utf-8").write(s)
print("apply-248:", n, "->", len(s))