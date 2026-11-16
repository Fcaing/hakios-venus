import io

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

# read the bhi identification registers before the doorbell
old = """				wr(bar0.base + 0x12c, 0);
				/* apply-176: star hands PBL the IOVA in its own page table"""
new = """				{
					uint32_t ver = rd(bar0.base + 0x100), maj = rd(bar0.base + 0x104);
					uint32_t serial = rd(bar0.base + 0x140), anti = rd(bar0.base + 0x144);
					uint32_t segs = rd(bar0.base + 0x148), hwid = rd(bar0.base + 0x14c);
					uint32_t ivec = rd(bar0.base + 0x120);

					printf("pcie: 5:   21: bhi id: ver 0x%08x maj 0x%08x serial 0x%08x anti 0x%08x segs 0x%08x hwid 0x%08x ivec 0x%08x\\n",
					       ver, maj, serial, anti, segs, hwid, ivec);
				}
				wr(bar0.base + 0x12c, 0);
				/* apply-176: star hands PBL the IOVA in its own page table"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

# the doorbell carries a nonzero session id, as the vendor does with prandom
old = """				wr(bar0.base + 0x110, PCIE_DMA_SIZE);
				wr(bar0.base + 0x118, 1);"""
new = """				wr(bar0.base + 0x110, PCIE_DMA_SIZE);
				{
					static uint32_t seed = 0x12345678u;
					uint32_t db;

					seed = seed * 1103515245u + 12345u;
					db = (seed >> 2) & 0x3fffffffu;
					if (db == 0) {
						db = 1;
					}
					wr(bar0.base + 0x118, db);
					printf("pcie: 5:   21: bhi doorbell 0x%08x\\n", db);
				}"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

# poll long enough for a real transfer (the vendor waits seconds)
old = """					for (i = 0; i < 30; i++) {
						uint32_t st = rd(bar0.base + 0x12c);

						if (((st >> 30) == 2 && rd(bar0.base + 0x128) == 1) ||
						    (st >> 30) == 3) {
							break;
						}
						sleep_ms(100);
					}"""
new = """					for (i = 0; i < 100; i++) {
						uint32_t st = rd(bar0.base + 0x12c);

						if (((st >> 30) == 2 && rd(bar0.base + 0x128) == 1) ||
						    (st >> 30) == 3) {
							break;
						}
						sleep_ms(100);
					}"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

io.open(p, "w", encoding="utf-8").write(s)
print("patched")