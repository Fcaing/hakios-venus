import io

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old = """	wr(smmu_mmio + 0x800 + 4 * smmu_match, 0x80000000u | PCIE_SMMU_STREAM);"""
new = """	/*
	 * apply-179: match every stream id for one run.  p180's guard test
	 * produced no fault at all, so either the endpoint never reads, or its
	 * stream id is not the 0x1c01 the OnePlus 9 reports.  With the mask
	 * wide open any translation miss has to show up in the context bank.
	 */
	wr(smmu_mmio + 0x800 + 4 * smmu_match, 0xffff0000u);"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

old = """	if (smr != (0x80000000u | PCIE_SMMU_STREAM) ||"""
new = """	if (smr != 0xffff0000u ||"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

io.open(p, "w", encoding="utf-8").write(s)
print("patched")