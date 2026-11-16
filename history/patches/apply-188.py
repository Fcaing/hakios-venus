import io

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old = """					printf("pcie: 5:   21: bhie soc 0x%08x status 0x%08x\\n",
					       rd(bar0.base + 0x224 + 0x00), rd(bar0.base + 0x224 + 0x44));
					wr(bar0.base + 0x224 + 0x2c, (uint32_t)PCIE_SMMU_IOVA);"""
new = """					printf("pcie: 5:   21: bhie soc 0x%08x status 0x%08x\\n",
					       rd(bar0.base + 0x224 + 0x00), rd(bar0.base + 0x224 + 0x44));
					/*
					 * apply-188: the status word was already
					 * SUCCESS for somebody else's session, so a
					 * successful poll proves nothing until it
					 * is cleared and our own sequence comes back.
					 */
					wr(bar0.base + 0x224 + 0x44, 0);
					wr(bar0.base + 0x224 + 0x2c, (uint32_t)PCIE_SMMU_IOVA);"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

io.open(p, "w", encoding="utf-8").write(s)
print("patched")