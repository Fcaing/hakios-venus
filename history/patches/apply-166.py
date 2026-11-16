import io
p = '/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c'
s = io.open(p, encoding='utf-8').read()
old = '''\t\t\t\t/* apply-164: the bhi upload, as the star port does it (lemonade_wifi.c:719). */
\t\t\t\tif (!need(&bar0)) {
\t\t\t\t\treturn;
\t\t\t\t}'''
new = '''\t\t\t\t/* apply-166: bar0 through kernel_map, and say whether it mapped at all. */
\t\t\t\tif (bar0.base == 0) {
\t\t\t\t\tbar0.base = ml_io_map_unmappable(bar0.phys, bar0.size, VM_WIMG_IO);
\t\t\t\t}
\t\t\t\tprintf("pcie: 5:   21: bar0 at 0x%x -> 0x%llx\\n", bar0.phys,
\t\t\t\t       (unsigned long long)bar0.base);
\t\t\t\tif (bar0.base == 0) {
\t\t\t\t\tprintf("pcie: 5:   21: bar0 would not map, stopping here\\n");
\t\t\t\t\tif (pcie_return) {
\t\t\t\t\t\tloader_return();
\t\t\t\t\t}
\t\t\t\t\treturn;
\t\t\t\t}'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('apply-166 ok')