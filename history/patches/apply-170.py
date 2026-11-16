import io
p = '/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c'
s = io.open(p, encoding='utf-8').read()
old1 = '''\t/* apply-168: say that the driver was called and hand the machine back, so the
\t * log can be read even when nothing else here is reached. */
\tprintf("pcie: the driver is called with pcie=%u, back to the loader (apply-168)\\n", asked);
\tloader_return();'''
new1 = '''\t/* apply-170: apply-168's early return removed; apply-169 returns at the end. */'''
assert s.count(old1) == 1, ('168', s.count(old1))
s = s.replace(old1, new1)
old2 = '''\t\t\t\t/* apply-167: back to the loader unconditionally: the dump is the only
\t\t\t\t * place any of this is visible, and a desktop makes the loader deaf. */
\t\t\t\tprintf("pcie: 5:   21: apply-167, back to the loader now\\n");
\t\t\t\tloader_return();'''
new2 = '''\t\t\t\t/* apply-170: apply-167's early return removed; apply-169 returns at the end. */'''
assert s.count(old2) == 1, ('167', s.count(old2))
s = s.replace(old2, new2)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('apply-170 ok')