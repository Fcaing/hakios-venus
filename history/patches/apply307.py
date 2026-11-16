import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

anchor = "wr(bar0.base + 0x300 + dch * 8, (uint32_t)trewp);"
assert s.count(anchor) == 1, ("anchor", s.count(anchor))
add = anchor + '''

						/* apply-307: if the device fetched from a bogus read pointer it would
						 * fault at the smmu.  Look right after the bell. */
						{
							uint32_t f7 = rd(smmu_cb + 0x58);
							uint32_t g7 = rd(smmu_mmio + 0x48);
							uint64_t a7 = ((uint64_t)rd(smmu_cb + 0x64) << 32) | rd(smmu_cb + 0x60);

							printf("apply-307 fsr after the bell: fsr 0x%08x far 0x%llx gfsr 0x%08x\\n",
							    f7, a7, g7);
						}'''
s = s.replace(anchor, add, 1)

old = '''printf("pcie: 5:   21: apply-297 t=%u ms'''
assert s.count(old) == 1
s = s.replace(old, '''printf("pcie: 5:   21: apply-297 fsr 0x%08x far 0x%llx\\n", rd(smmu_cb + 0x58), ((uint64_t)rd(smmu_cb + 0x64) << 32) | rd(smmu_cb + 0x60));
								printf("pcie: 5:   21: apply-297 t=%u ms''', 1)

io.open(p, "w", encoding="utf-8").write(s)
print("apply-307 applied")