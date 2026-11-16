import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

def sub1(old, new):
    assert s.count(old) == 1, "not unique: %r" % old[:60]
    return s.replace(old, new, 1)

anchor = '\tPCIE_READ(5, "the branch status of the auxiliary clock, 0x6b028", gcc.base + 0x6b028);\n'
assert s.count(anchor) == 1

probe = anchor + '''
	printf("pcie: 1: apply-230: cfg_ahb 0x6b024 0x%08x (halt bit31 %u), pipe_src 0x6b054 0x%08x, aux_src 0x6b058 0x%08x (halt 0x%08x), aux_cfg 0x6b05c 0x%08x, rchng_src 0x6b03c 0x%08x, rchng_cfg 0x6b040 0x%08x\\n",
	    rd(gcc.base + 0x6b024), rd(gcc.base + 0x6b024) >> 31, rd(gcc.base + 0x6b054),
	    rd(gcc.base + 0x6b058), rd(gcc.base + 0x6b058 + 4), rd(gcc.base + 0x6b05c),
	    rd(gcc.base + 0x6b03c), rd(gcc.base + 0x6b040));
'''
s = sub1(anchor, probe)
io.open(p, "w", encoding="utf-8").write(s)
print("ok probe 230")