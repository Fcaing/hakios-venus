import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

a1 = "\t\t\t\t\twr(bar0.base + 0x224 + 0x3c, seq);\n"
assert s.count(a1) == 1
s = s.replace(a1, a1 + """\t\t\t\t\tprintf("pcie: 5:   21: apply-263 right after the bhie bell: mh 0x%08x ee 0x%08x err 0x%08x\\n",
\t\t\t\t\t    rd(bar0.base + 0x48), rd(bar0.base + 0x128), rd(bar0.base + 0x130));
""")

a2 = """\t\t\t\t\tprintf("pcie: 5:   21: bhie after %u ms: status 0x%08x (top %u, seq 0x%08x) ee 0x%08x fsr 0x%08x far 0x%08x:%08x\\n",
\t\t\t\t\t    (unsigned)off, st, st >> 30, st & 0x3fffffffu, rd(bar0.base + 0x128),
\t\t\t\t\t    rd(smmu_cb + 0x58), rd(smmu_cb + 0x64), rd(smmu_cb + 0x60));"""
assert s.count(a2) == 1
s = s.replace(a2, """\t\t\t\t\tprintf("pcie: 5:   21: bhie after %u ms: status 0x%08x (top %u, seq 0x%08x) ee 0x%08x mh 0x%08x fsr 0x%08x far 0x%08x:%08x\\n",
\t\t\t\t\t    (unsigned)off, st, st >> 30, st & 0x3fffffffu, rd(bar0.base + 0x128),
\t\t\t\t\t    rd(bar0.base + 0x48), rd(smmu_cb + 0x58), rd(smmu_cb + 0x64), rd(smmu_cb + 0x60));""")
io.open(p, "w", encoding="utf-8").write(s)
print("apply-263 inserted")