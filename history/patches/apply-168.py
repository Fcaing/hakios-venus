import io
p = '/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c'
s = io.open(p, encoding='utf-8').read()
old = '''\tif (!PE_parse_boot_argn("pcie", &asked, sizeof(asked)) || asked == 0) {
\t\treturn;                         /* nothing here is touched unless asked for */
\t}'''
new = '''\tif (!PE_parse_boot_argn("pcie", &asked, sizeof(asked)) || asked == 0) {
\t\treturn;                         /* nothing here is touched unless asked for */
\t}
\t/* apply-168: say that the driver was called and hand the machine back, so the
\t * log can be read even when nothing else here is reached. */
\tprintf("pcie: the driver is called with pcie=%u, back to the loader (apply-168)\\n", asked);
\tloader_return();'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('apply-168 ok')