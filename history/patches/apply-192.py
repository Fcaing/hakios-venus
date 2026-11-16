import io

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old = """		kr = kmem_alloc_contig(kernel_map, &buffer, PCIE_DMA_SIZE, PAGE_MASK, 0, 0,"""
new = """		/*
		 * apply-192: p191's ERRDBG1/ERRDBG3 hold the guard address we rang
		 * with, and no SMMU fault ever came.  PBL reads through the physical
		 * address space and only the low 4 GiB is addressable from there, so
		 * ask for a page under that limit (max_pnum counts 4 KiB pages).
		 */
		kr = kmem_alloc_contig(kernel_map, &buffer, PCIE_DMA_SIZE, 0, 0xfffff, 0,"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("patched")