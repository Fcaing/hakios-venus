import io

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old = """				/*
				 * apply-187: BHIEOFF reads 0x224, and 0x224's first word"""
new = """				/*
				 * apply-190: dump the whole BHI window, most of it
				 * never read before; the answer to "why does PBL
				 * ignore us" is likely one of these words.
				 */
				{
					uint32_t off;

					for (off = 0x100; off <= 0x15c; off += 4) {
						printf("pcie: 5:   21: bhi[0x%03x] = 0x%08x\\n",
						       off, rd(bar0.base + off));
					}
				}
				/*
				 * apply-187: BHIEOFF reads 0x224, and 0x224's first word"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

io.open(p, "w", encoding="utf-8").write(s)
print("patched")