import io

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old = """				{
					uint32_t st = rd(bar0.base + 0x12c);
					printf("pcie: 5:   21: bhi after: status 0x%08x (top %u, ee %u) mhi 0x%08x err 0x%08x\\n",
					       st, st >> 30, st & 0xff, rd(bar0.base + 0x100), rd(bar0.base + 0x130));"""
new = """				/*
				 * apply-187: BHIEOFF reads 0x224, and 0x224's first word
				 * is the soc id the vendor calls BHIE_MSMSOCID.  So the
				 * endpoint has a second, larger mailbox that the vendor
				 * uses for the full amss image.  Try a 512 KiB slice.
				 */
				{
					uint32_t st;

					printf("pcie: 5:   21: bhie soc 0x%08x status 0x%08x\\n",
					       rd(bar0.base + 0x224 + 0x00), rd(bar0.base + 0x224 + 0x44));
					wr(bar0.base + 0x224 + 0x2c, (uint32_t)PCIE_SMMU_IOVA);
					wr(bar0.base + 0x224 + 0x30, (uint32_t)(PCIE_SMMU_IOVA >> 32));
					wr(bar0.base + 0x224 + 0x34, PCIE_DMA_SIZE);
					wr(bar0.base + 0x224 + 0x3c, 0x2dc6454u);
					{
						uint32_t i;

						for (i = 0; i < 100; i++) {
							st = rd(bar0.base + 0x224 + 0x44);
							if ((st >> 30) == 2 || (st >> 30) == 3) {
								break;
							}
							sleep_ms(30);
						}
					}
					printf("pcie: 5:   21: bhie after: status 0x%08x (top %u, seq 0x%08x) after %u polls\\n",
					       st, st >> 30, st & 0x3fffffffu, i);
					pcie_note("bhie 0x%08x; ", st);
				}
				{
					uint32_t st = rd(bar0.base + 0x12c);
					printf("pcie: 5:   21: bhi after: status 0x%08x (top %u, ee %u) mhi 0x%08x err 0x%08x\\n",
					       st, st >> 30, st & 0xff, rd(bar0.base + 0x100), rd(bar0.base + 0x130));"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

io.open(p, "w", encoding="utf-8").write(s)
print("patched")