import io

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old = """					wr(bar0.base + 0x224 + 0x34, PCIE_DMA_SIZE);
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
					       st, st >> 30, st & 0x3fffffffu, i);"""
new = """					/*
					 * apply-189: claim the whole amss image while
					 * only 512 KiB is mapped.  If PBL starts the
					 * transfer at all it will walk off the end of
					 * the table and leave a fault we can see.
					 */
					wr(bar0.base + 0x224 + 0x34, 0x004fe650u);
					wr(bar0.base + 0x224 + 0x3c, 0x2dc6454u);
					{
						uint32_t i, fsr = 0;

						for (i = 0; i < 200; i++) {
							st = rd(bar0.base + 0x224 + 0x44);
							fsr = rd(smmu_cb + 0x58);
							if ((st >> 30) == 2 || (st >> 30) == 3 ||
							    (fsr & PCIE_SMMU_FAULT)) {
								break;
							}
							sleep_ms(30);
						}
						printf("pcie: 5:   21: bhie big: fsr 0x%08x far 0x%08x:0x%08x after %u polls\\n",
						       fsr, rd(smmu_cb + 0x60), rd(smmu_cb + 0x64), i);
						wr(smmu_cb + 0x58, fsr & PCIE_SMMU_FAULT);
					}
					printf("pcie: 5:   21: bhie after: status 0x%08x (top %u, seq 0x%08x)\\n",
					       st, st >> 30, st & 0x3fffffffu);"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

io.open(p, "w", encoding="utf-8").write(s)
print("patched")