import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old = """\t\t\t\t\t\tprintf("pcie: 5:   21: pt l1[2] 0x%016llx l2[256] 0x%016llx l3[4] 0x%016llx dma kvtophys 0x%llx\\n",
\t\t\t\t\t\t    (unsigned long long)pt1[2], (unsigned long long)pt2[256],
\t\t\t\t\t\t    (unsigned long long)pt3[4],
\t\t\t\t\t\t    (unsigned long long)kvtophys(pcie_dma));"""
assert s.count(old) == 1, s.count(old)
new = """\t\t\t\t\t\tprintf("pcie: 5:   21: pt l1[2] 0x%016llx l2[256] 0x%016llx l3[4] 0x%016llx dma kvtophys 0x%llx\\n",
\t\t\t\t\t\t    (unsigned long long)pt1[2], (unsigned long long)pt2[256],
\t\t\t\t\t\t    (unsigned long long)pt3[4],
\t\t\t\t\t\t    (unsigned long long)kvtophys(pcie_dma));
\t\t\t\t\t\t{
\t\t\t\t\t\t\tuint32_t k;
\t\t\t\t\t\t\tfor (k = 0; k < 8; k++) {
\t\t\t\t\t\t\t\tprintf("pcie: 5:   21: l3[%u] 0x%016llx kvtophys 0x%llx\\n", k,
\t\t\t\t\t\t\t\t    (unsigned long long)pt3[k],
\t\t\t\t\t\t\t\t    (unsigned long long)kvtophys(pcie_dma + k * PAGE_SIZE));
\t\t\t\t\t\t\t}
\t\t\t\t\t\t}"""
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("ok apply-213")