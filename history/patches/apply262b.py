import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
old = '''\t\t\t\t\tif (PE_parse_boot_argn("pcie_msi_test", &want, sizeof(want)) && want != 0) {
\t\t\t\t\t\tue = (uint32_t)PCIE_SMMU_VEC_IOVA;
\t\t\t\t\t\twr(conf.base + 0x58, 0x00001234u);
\t\t\t\t\t\tprintf("pcie: 5:   21: apply-262 msi re-armed with data 0x00001234 at 0x%08x\\n", ue);'''
new = '''\t\t\t\t\t{
\t\t\t\t\t\tuint32_t want2 = 0;

\t\t\t\t\t\tPE_parse_boot_argn("pcie_msi_test", &want2, sizeof(want2));
\t\t\t\t\t\tif (want2 != 0) {
\t\t\t\t\t\tuint32_t ue = (uint32_t)PCIE_SMMU_VEC_IOVA;
\t\t\t\t\t\twr(conf.base + 0x58, 0x00001234u);
\t\t\t\t\t\tprintf("pcie: 5:   21: apply-262 msi re-armed with data 0x00001234 at 0x%08x\\n", ue);'''
assert s.count(old) == 1
s = s.replace(old, new)
# close the two extra braces where the old single brace closed
old2 = '''\t\t\t\t\t\t\tsleep_ms(10);
\t\t\t\t\t\t}
\t\t\t\t\t}
'''
assert s.count(old2) == 1
s = s.replace(old2, '''\t\t\t\t\t\t\tsleep_ms(10);
\t\t\t\t\t\t}
\t\t\t\t\t\t}
\t\t\t\t\t}
''')
io.open(p, "w", encoding="utf-8").write(s)
print("fixed braces")