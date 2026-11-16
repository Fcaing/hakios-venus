import io

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

# revert the wide-mask experiment: the SMMU refused 0xffff0000 (read back 0).
old = """	wr(smmu_mmio + 0x800 + 4 * smmu_match, 0xffff0000u);"""
new = """	wr(smmu_mmio + 0x800 + 4 * smmu_match, 0x80000000u | PCIE_SMMU_STREAM);"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

old = """	if (smr != 0xffff0000u ||"""
new = """	if (smr != (0x80000000u | PCIE_SMMU_STREAM) ||"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

# read MHICTRL / MHISTATUS and clear the reset bit if it is set.
old = """				printf("pcie: 5:   21: bar0 0x128 = 0x%08x (star wants 0)\\n", rd(bar0.base + 0x128));"""
new = """				printf("pcie: 5:   21: bar0 0x128 = 0x%08x (star wants 0)\\n", rd(bar0.base + 0x128));
				/*
				 * apply-180: the MHI control register was never looked at.
				 * mhi_pm.c clears MHICTRL bit 1 (RESET) before it hands the
				 * device to MHI; while it is set no image transfer can
				 * start and BHI_STATUS stays at RESET (0).
				 */
				{
					uint32_t ctrl = rd(bar0.base + 0x38);
					uint32_t stat = rd(bar0.base + 0x48);

					printf("pcie: 5:   21: mhi ctrl 0x%08x status 0x%08x (reset %u ready %u state 0x%02x)\\n",
					       ctrl, stat, ctrl & 2u, stat & 1u, (stat >> 8) & 0xffu);
					if (ctrl & 2u) {
						wr(bar0.base + 0x38, ctrl & ~2u);
						sleep_ms(20);
						printf("pcie: 5:   21: mhi reset cleared: 0x%08x -> 0x%08x\\n",
						       ctrl, rd(bar0.base + 0x38));
					}
				}"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

io.open(p, "w", encoding="utf-8").write(s)
print("patched")