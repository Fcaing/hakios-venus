import io

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old = """					wr(bar0.base + 0x118, 1);
					for (i = 0; i < 2000; i++) {"""
new = """					wr(bar0.base + 0x118, 1);
					printf("pcie: 5:   21: bhi regs after the write: addr 0x%08x:0x%08x size 0x%08x db 0x%08x status 0x%08x\\n",
					       rd(bar0.base + 0x10c), rd(bar0.base + 0x108),
					       rd(bar0.base + 0x110), rd(bar0.base + 0x118),
					       rd(bar0.base + 0x12c));
					for (i = 0; i < 2000; i++) {"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

io.open(p, "w", encoding="utf-8").write(s)
print("patched")