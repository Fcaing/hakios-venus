import io

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old = """	wr(smmu_mmio + 0x800 + 4 * smmu_match, 0x80000000u | PCIE_SMMU_STREAM);"""
new = """	/*
	 * apply-183: the real dts says iommu-map = <0x0  &smmu 0x1c00 0x1>,
	 * <0x100 &smmu 0x1c01 0x1>, so the root complex itself is stream
	 * 0x1c00 and the endpoint 0x1c01.  p183 showed the doorbell register
	 * takes the write while nothing ever reaches the SMMU: if the
	 * endpoint's own DMA uses the root complex stream, an exact 0x1c01
	 * match would bypass it silently.  Match both with a one bit mask.
	 */
	wr(smmu_mmio + 0x800 + 4 * smmu_match, 0x80000000u | (1u << 16) | 0x1c00u);"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

old = """	if (smr != (0x80000000u | PCIE_SMMU_STREAM) ||"""
new = """	if (smr != (0x80000000u | (1u << 16) | 0x1c00u) ||"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

io.open(p, "w", encoding="utf-8").write(s)
print("patched")