import io

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old = """				printf("pcie: 5:   21: bhi before: soc 0x%08x ee 0x%08x mhi 0x%08x status 0x%08x err 0x%08x\\n","""
new = """				/*
				 * apply-195: star saves and restores iATU region 1 through the
				 * DBI mirror (dbi + 0x1200); region 1 is the outbound window a
				 * device uses to reach host memory.  Read it before anything
				 * else, so we learn what the loader left behind.
				 */
				printf("pcie: 5:   21: iatu region 1 (dbi+0x1200): "
				    "%08x %08x %08x %08x %08x %08x %08x\\n",
				    rd(dbi.base + 0x1200), rd(dbi.base + 0x1204), rd(dbi.base + 0x1208),
				    rd(dbi.base + 0x120c), rd(dbi.base + 0x1210), rd(dbi.base + 0x1214),
				    rd(dbi.base + 0x1218));
				printf("pcie: 5:   21: iatu region 0 (dbi+0x1000): "
				    "%08x %08x %08x %08x %08x %08x %08x\\n",
				    rd(dbi.base + 0x1000), rd(dbi.base + 0x1004), rd(dbi.base + 0x1008),
				    rd(dbi.base + 0x100c), rd(dbi.base + 0x1010), rd(dbi.base + 0x1014),
				    rd(dbi.base + 0x1018));
				printf("pcie: 5:   21: bhi before: soc 0x%08x ee 0x%08x mhi 0x%08x status 0x%08x err 0x%08x\\n","""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("patched")