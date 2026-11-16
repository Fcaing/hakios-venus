import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
old = """				wr(bar0.base + 0x10c, (uint32_t)(pcie_dma_pa >> 32));
				wr(bar0.base + 0x108, (uint32_t)pcie_dma_pa);"""
new = """				wr(bar0.base + 0x10c, 0u);
				wr(bar0.base + 0x108, 0xa0000000u);"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("patched")