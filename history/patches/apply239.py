import io, sys
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(p, "r", encoding="utf-8", errors="surrogateescape").read()
anchor = """							wr(bar0.base + 0x224 + 0x30,
								(uint32_t)(PCIE_SMMU_VEC_IOVA >> 32));
							wr(bar0.base + 0x224 + 0x2c,
								(uint32_t)PCIE_SMMU_VEC_IOVA);
							wr(bar0.base + 0x224 + 0x34, nvec * 16);
"""
assert s.count(anchor) == 1, s.count(anchor)
new = """							{
								uint32_t nove = 0;
								if (PE_parse_boot_argn("pcie_novec", &nove, sizeof(nove)) && nove != 0) {
									printf("pcie: 5:   21: apply-239: bhie registers left untouched (novec) tx 0x%08x size 0x%08x\\n",
									    rd(bar0.base + 0x224 + 0x2c), rd(bar0.base + 0x224 + 0x34));
								} else {
							wr(bar0.base + 0x224 + 0x30,
								(uint32_t)(PCIE_SMMU_VEC_IOVA >> 32));
							wr(bar0.base + 0x224 + 0x2c,
								(uint32_t)PCIE_SMMU_VEC_IOVA);
							wr(bar0.base + 0x224 + 0x34, nvec * 16);
								}
							}
"""
s = s.replace(anchor, new)
open(p, "w", encoding="utf-8", errors="surrogateescape").write(s)
print("patched, apply-239 count:", s.count("apply-239"))