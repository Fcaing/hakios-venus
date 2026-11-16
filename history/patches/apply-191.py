import io

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old = """				wr(bar0.base + 0x12c, 0);
				/* apply-176: star hands PBL the IOVA in its own page table
				 * (WIFI_DMA_IOVA 0xa0004000), never a physical address. */
				wr(bar0.base + 0x10c, (uint32_t)(PCIE_SMMU_IOVA >> 32));
				wr(bar0.base + 0x108, (uint32_t)PCIE_SMMU_IOVA);"""
new = """				wr(bar0.base + 0x12c, 0);
				/*
				 * apply-191: p191 showed ERRDBG1/ERRDBG3 holding the
				 * exact guard address and size we rang with, and no
				 * SMMU fault ever appeared.  PBL therefore does read,
				 * but its reads never reach the SMMU: it walks the
				 * physical address space.  Hand it the real page.
				 */
				wr(bar0.base + 0x10c, (uint32_t)(pcie_dma_pa >> 32));
				wr(bar0.base + 0x108, (uint32_t)pcie_dma_pa);"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

# the guard test stays on the iova: it is only there to probe the smmu path.

io.open(p, "w", encoding="utf-8").write(s)
print("patched")