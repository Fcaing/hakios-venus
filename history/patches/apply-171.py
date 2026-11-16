import io
p = '/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c'
s = io.open(p, encoding='utf-8').read()
old = '''\t\t\twlan_en();
\t\t\tperst(false);
\t\t\tsleep_ms(20);
\t\t\tgen1_config();
\t\t\tsleep_ms(10);
\t\t\tperst(true);
\t\t\tsleep_ms(20);
\t\t\tlink_train_start();'''
new = '''\t\t\twlan_en();
\t\t\t/* apply-171: the vendor holds PERST# low for 100 ms before it lets go
\t\t\t * (msm_pcie_link_train), not the 20 this port used; the link comes up
\t\t\t * some boots and not others, which is what a marginal t_PVPERL looks
\t\t\t * like.  Three 100 ms stretches: p160 proved that much sleep is safe. */
\t\t\tperst(false);
\t\t\tsleep_ms(100);
\t\t\tgen1_config();
\t\t\tsleep_ms(100);
\t\t\tperst(true);
\t\t\tsleep_ms(100);
\t\t\tlink_train_start();'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('apply-171 ok')