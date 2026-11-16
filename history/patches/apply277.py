import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
n0 = len(s)

a = "wr(bar0.base + 0x10, (cf & ~0xff000000u) | (2u << 24) | (3u << 16));"
assert s.count(a) == 1
s = s.replace(a, """wr(bar0.base + 0x10, (cf & 0x0000ffffu) | (3u << 16));""")

a2 = 'printf("pcie: 5:   21: apply-269 mhicfg 0x%08x -> 0x%08x\\n",'
assert s.count(a2) == 1
s = s.replace(a2, 'printf("pcie: 5:   21: apply-277 mhicfg 0x%08x -> 0x%08x (star style, nhwer cleared)\\n",')

io.open(p, "w", encoding="utf-8").write(s)
print("ok", n0, "->", len(s))