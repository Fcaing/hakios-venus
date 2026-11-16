import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
n0 = len(s)

a = """wr(pcie_dma_extra + 0x2400 + 0x28, (uint32_t)cwp);
					wr(pcie_dma_extra + 0x2400 + 0x2c, (uint32_t)(cwp >> 32));"""
assert s.count(a) == 1, s.count(a)
s = s.replace(a, """/* apply-275: the packed layout puts rbase at 0x0c, rlen at 0x14,
					 * rp at 0x1c and wp at 0x24; writing wp at 0x28 landed past
					 * the end of the structure. */
					wr(pcie_dma_extra + 0x2400 + 0x0c, (uint32_t)cbase);
					wr(pcie_dma_extra + 0x2400 + 0x10, 0);
					wr(pcie_dma_extra + 0x2400 + 0x14, 0x1000);
					wr(pcie_dma_extra + 0x2400 + 0x1c, (uint32_t)cbase);
					wr(pcie_dma_extra + 0x2400 + 0x20, 0);
					wr(pcie_dma_extra + 0x2400 + 0x24, (uint32_t)cwp);
					wr(pcie_dma_extra + 0x2400 + 0x28, (uint32_t)(cwp >> 32));""")

a2 = "rd(pcie_dma_extra + 0x2020), rd(pcie_dma_extra + 0x2028),"
n = s.count(a2)
s = s.replace(a2, "rd(pcie_dma_extra + 0x201c), rd(pcie_dma_extra + 0x2024),")

io.open(p, "w", encoding="utf-8").write(s)
print("ok", n0, "->", len(s), "a2 replaced", n)