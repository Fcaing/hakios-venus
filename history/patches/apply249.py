import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
n = len(s)

# the old apply-220 block: enable bit is bit 16 of the word at 0x50
a = """\t\t\t\t\twr(conf.base + 0x5c, 0u);
\t\t\t\t\twr(conf.base + 0x50, (cap & 0xffff0000u) | ((cap & 0xfffeu) | 1u));
\t\t\t\t\tenabled = rd(conf.base + 0x50);
\t\t\t\t\tprintf("pcie: 5:   21: msi after: cap 0x%08x (enabled %u, vectors %u, mask 0x%08x)\\n",
\t\t\t\t\t       enabled, enabled & 1u, (enabled >> 1) & 7u, rd(conf.base + 0x5c));"""
assert s.count(a) == 1, s.count(a)
s = s.replace(a, """\t\t\t\t\t/*
\t\t\t\t\t * apply-249: the enable bit is bit 0 of the 16 bit message
\t\t\t\t\t * control at 0x52, which is bit 16 of the word at 0x50.
\t\t\t\t\t * This used to OR a 1 into the low half, i.e. into the
\t\t\t\t\t * capability id, and the control word never changed --
\t\t\t\t\t * so the endpoint was never told to send an msi at all.
\t\t\t\t\t */
\t\t\t\t\twr(conf.base + 0x5c, 0u);
\t\t\t\t\twr(conf.base + 0x50, cap | (1u << 16));
\t\t\t\t\tenabled = rd(conf.base + 0x50);
\t\t\t\t\tprintf("pcie: 5:   21: msi after: cap 0x%08x (control 0x%04x enabled %u vectors %u, mask 0x%08x)\\n",
\t\t\t\t\t       enabled, (enabled >> 16) & 0xffffu, (enabled >> 16) & 1u,
\t\t\t\t\t       ((enabled >> 16) >> 1) & 7u, rd(conf.base + 0x5c));""")

# the apply-246 arming block
b = """\t\t\t\t\t\twr(conf.base + doff, 0x00005a5au);
\t\t\t\t\t\twr(conf.base + 0x50, (cap & 0xffff0000u) |
\t\t\t\t\t\t    ((cap & 0xfffeu) | 1u));"""
assert s.count(b) == 1, s.count(b)
s = s.replace(b, """\t\t\t\t\t\twr(conf.base + doff, 0x00005a5au);
\t\t\t\t\t\twr(conf.base + 0x50, cap | (1u << 16));""")

io.open(p, "w", encoding="utf-8").write(s)
print("apply-249:", n, "->", len(s))