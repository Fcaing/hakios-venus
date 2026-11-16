import io

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old = """					wr(smmu_cb + 0x7f0, 0);
					sleep_ms(2);
					guard = PCIE_SMMU_IOVA + PCIE_DMA_SIZE;
					uint32_t fsr = 0, i;"""
new = """					wr(smmu_cb + 0x7f0, 0);
					sleep_ms(2);
				}
				{
					uint64_t guard = PCIE_SMMU_IOVA + PCIE_DMA_SIZE;
					uint32_t fsr = 0, i;"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

io.open(p, "w", encoding="utf-8").write(s)
print("patched")