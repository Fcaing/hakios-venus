import io
p = '/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c'
s = io.open(p, encoding='utf-8').read()
old = '''\t\t\t\tprintf("pcie: 5:   21: bar0 at 0x%x -> 0x%llx\\n", bar0.phys,
\t\t\t\t       (unsigned long long)bar0.base);'''
new = '''\t\t\t\tprintf("pcie: 5:   21: bar0 at 0x%x -> 0x%llx\\n", bar0.phys,
\t\t\t\t       (unsigned long long)bar0.base);
\t\t\t\t/* apply-167: back to the loader unconditionally: the dump is the only
\t\t\t\t * place any of this is visible, and a desktop makes the loader deaf. */
\t\t\t\tprintf("pcie: 5:   21: apply-167, back to the loader now\\n");
\t\t\t\tloader_return();'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('apply-167 ok')