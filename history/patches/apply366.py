P = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
src = open(P).read()

# 1. parse pcie_erfull early
a = '\tPE_parse_boot_argn("pcie_ee2m0", &pcie_ee2m0, sizeof(pcie_ee2m0));'
assert src.count(a) == 1, ("parse", src.count(a))
src = src.replace(a, a + '\n\tPE_parse_boot_argn("pcie_erfull", &pcie_erfull, sizeof(pcie_erfull));\t/* apply-366 */')

# 2. the two legacy 0x30 channel-context reads -> the packed 0x2c layout
b = """					    rd(pcie_dma_extra + 20 * 0x30 + 0x20), rd(pcie_dma_extra + 20 * 0x30 + 0x28));"""
assert src.count(b) == 1, ("b", src.count(b))
src = src.replace(b, """					    rd(pcie_dma_extra + 20 * 0x2c + 0x1c), rd(pcie_dma_extra + 20 * 0x2c + 0x24));\t/* apply-366 */""")

# 3. the er context print: offsets were 0x10/0x18/0x20/0x28 (legacy), the packed layout is 0x0c/0x14/0x1c/0x24
c = """						    w, rd(pcie_dma_extra + 0x2000 + w * 0x30 + 0x10),
						    rd(pcie_dma_extra + 0x2000 + w * 0x30 + 0x18),
						    rd(pcie_dma_extra + 0x2000 + w * 0x30 + 0x20),
						    rd(pcie_dma_extra + 0x2000 + w * 0x30 + 0x28),"""
assert src.count(c) == 1, ("c", src.count(c))
src = src.replace(c, """						    w, rd(pcie_dma_extra + 0x2000 + w * 0x30 + 0x0c),
						    rd(pcie_dma_extra + 0x2000 + w * 0x30 + 0x14),
						    rd(pcie_dma_extra + 0x2000 + w * 0x30 + 0x1c),
						    rd(pcie_dma_extra + 0x2000 + w * 0x30 + 0x24),""")

open(P, "w").write(src)
print("apply-366 ok")
