import io
p = '/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c'
s = io.open(p, encoding='utf-8').read()
old = '''\t\t\tprintf("pcie: watch %u of %u s\\n", i + 1, pcie_watch_seconds);
\t\t\tsleep_ms(1000);
\t\t}
\t}
}'''
new = '''\t\t\tprintf("pcie: watch %u of %u s\\n", i + 1, pcie_watch_seconds);
\t\t\tsleep_ms(1000);
\t\t}
\t}

\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */
\tprintf("pcie: the probe is done, back to the loader (apply-169)\\n");
\tloader_return();
}'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('apply-169 ok')