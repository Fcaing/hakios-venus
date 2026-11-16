import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old = "\t\t\t\t\twr(bar0.base + 0x118, db);\n\t\t\t\t\tprintf(\"pcie: 5:   21: bhi doorbell 0x%08x\\n\", db);"
assert s.count(old) == 1, s.count(old)
new = ("""\t\t\t\t\tif (smmu_state == 1) {
\t\t\t\t\t\tprintf("pcie: 5:   21: fsr before doorbell 0x%08x gfsr 0x%08x far 0x%08x:%08x\\n",
\t\t\t\t\t\t    rd(smmu_cb + 0x58), rd(smmu_mmio + 0x48),
\t\t\t\t\t\t    rd(smmu_cb + 0x64), rd(smmu_cb + 0x60));
\t\t\t\t\t}
\t\t\t\t\twr(bar0.base + 0x118, db);
\t\t\t\t\tprintf("pcie: 5:   21: bhi doorbell 0x%08x\\n", db);""")
s = s.replace(old, new, 1)

old2 = ("\t\t\t\t/*\n\t\t\t\t * apply-190: dump the whole BHI window, most of it\n"
        "\t\t\t\t * never read before; the answer to \"why does PBL\n\t\t\t\t * ignore us\" is likely one of these words.\n\t\t\t\t */")
assert s.count(old2) == 1, s.count(old2)
new2 = ("""\t\t\t\tif (smmu_state == 1) {
\t\t\t\t\tprintf("pcie: 5:   21: fsr after doorbell 0x%08x gfsr 0x%08x far 0x%08x:%08x\\n",
\t\t\t\t\t    rd(smmu_cb + 0x58), rd(smmu_mmio + 0x48),
\t\t\t\t\t    rd(smmu_cb + 0x64), rd(smmu_cb + 0x60));
\t\t\t\t}
""" + old2)
s = s.replace(old2, new2, 1)

io.open(p, "w", encoding="utf-8").write(s)
print("ok apply-211")