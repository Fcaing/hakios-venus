import io
p = '/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c'
s = io.open(p, encoding='utf-8').read()
# 1. extern declaration next to the other extern
old0 = 'extern void loader_log_putc(char c);'
assert s.count(old0) == 1, ('putc', s.count(old0))
s = s.replace(old0, old0 + '\nextern void loader_return(void);\t/* apply-165: come back to the loader for the log */')
# 2. the return itself, after the bhi report
old = '''\t\t\t\t\tpcie_note("bhi 0x%08x mhi 0x%08x err 0x%08x; ", st,
\t\t\t\t\t          rd(bar0.base + 0x100), rd(bar0.base + 0x130));
\t\t\t\t}
\t\t\t\treturn;'''
new = '''\t\t\t\t\tpcie_note("bhi 0x%08x mhi 0x%08x err 0x%08x; ", st,
\t\t\t\t\t          rd(bar0.base + 0x100), rd(bar0.base + 0x130));
\t\t\t\t}
\t\t\t\t/* apply-165: hand the machine back so the dump can be read. */
\t\t\t\tif (pcie_return) {
\t\t\t\t\tprintf("pcie: 5:   21: pcie_return=1, back to the loader now\\n");
\t\t\t\t\tsleep_ms(100);
\t\t\t\t\tloader_return();
\t\t\t\t}
\t\t\t\treturn;'''
assert s.count(old) == 1, ('bhi', s.count(old))
s = s.replace(old, new)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('apply-165 ok')