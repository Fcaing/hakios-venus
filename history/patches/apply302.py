import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
old = """					if (smmu_state == 1 && pcie_dma_extra != 0) {
						volatile uint32_t *cc2 = (volatile uint32_t *)(pcie_dma_extra + 0x2400);"""
new = """					/* apply-302: the DT marks ch20/ch21 as mhi,auto-start, so the
					 * device starts them itself on entering mission mode; sending
					 * our own START_CHAN may be what corrupts the context. */
					if (pcie_chanstart != 0 && smmu_state == 1 && pcie_dma_extra != 0) {
						volatile uint32_t *cc2 = (volatile uint32_t *)(pcie_dma_extra + 0x2400);"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-302 patched")