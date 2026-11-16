import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

# 1. declaration after pcie_mhi_data (line 89 style: with a comment)
old = "static uint32_t pcie_mhi_data;\t/* apply-292: push one data tre at the ipcr tx channel */"
assert s.count(old) == 1, s.count(old)
s = s.replace(old, old + "\nstatic uint32_t pcie_trap;\t/* apply-312: point the ring at an unmapped address */")

# 2. parse the knob next to pcie_mhi_data
anchor = """								d2 = 0;
								if (PE_parse_boot_argn("pcie_mhi_data", &d2, sizeof(d2))) {
									pcie_mhi_data = d2;
								}"""
assert s.count(anchor) == 1, s.count(anchor)
s = s.replace(anchor, anchor + """
								d2 = 0;
								if (PE_parse_boot_argn("pcie_trap", &d2, sizeof(d2))) {
									pcie_trap = d2;
								}""")

# 3. the experiment, after the data tre printout
T = "\t" * 6
anchor2 = T + 'printf("pcie: 5:   21: apply-292 send: tre ptr 0x%08x len 0x%08x dw1 0x%08x ch20 wp 0x%08x\\n",'
assert s.count(anchor2) == 1, s.count(anchor2)
tail_marker = "rd(pcie_dma_extra + dch * 0x2c + 0x24));"
idx = s.index(tail_marker, s.index(anchor2))
end = s.index("\n", idx) + 1
block = (
    T + "/* apply-312: point the ring at an address that has no mapping at all.\n"
    + T + " * If the device really walks the ring it has to fault there.\n"
    + T + " */\n"
    + T + "if (pcie_trap != 0) {\n"
    + T + "\tuint32_t tr;\n"
    + T + "\twr(smmu_cb + 0x58, rd(smmu_cb + 0x58));\n"
    + T + "\twr(smmu_mmio + 0x48, rd(smmu_mmio + 0x48));\n"
    + T + "\twr(pcie_dma_extra + dch * 0x2c + 0x0c, 0xa0100000u);\n"
    + T + "\twr(pcie_dma_extra + dch * 0x2c + 0x14, 0x400u);\n"
    + T + "\twr(pcie_dma_extra + dch * 0x2c + 0x1c, 0xa0100000u);\n"
    + T + "\twr(pcie_dma_extra + dch * 0x2c + 0x20, 0u);\n"
    + T + "\twr(pcie_dma_extra + dch * 0x2c + 0x24, 0xa0100010u);\n"
    + T + "\twr(pcie_dma_extra + dch * 0x2c + 0x28, 0u);\n"
    + T + "\t__asm__ volatile (\"dsb sy\" : : : \"memory\");\n"
    + T + "\twr(bar0.base + 0x300 + dch * 8, 0xa0100010u);\n"
    + T + "\tfor (tr = 0; tr < 200; tr++) {\n"
    + T + "\t\tsleep_ms(5);\n"
    + T + "\t\tif (rd(smmu_cb + 0x58) & 2u) {\n"
    + T + "\t\t\tbreak;\n"
    + T + "\t\t}\n"
    + T + "\t}\n"
    + T + '\tprintf("pcie: 5:   21: apply-312 trap: after %u ms fsr 0x%08x far 0x%08x:%08x gfsr 0x%08x ch20 rp 0x%08x wp 0x%08x mh 0x%08x ee 0x%08x\\n",\n'
    + T + "\t    tr * 5, rd(smmu_cb + 0x58), rd(smmu_cb + 0x64), rd(smmu_cb + 0x60),\n"
    + T + "\t    rd(smmu_mmio + 0x48), rd(pcie_dma_extra + dch * 0x2c + 0x1c),\n"
    + T + "\t    rd(pcie_dma_extra + dch * 0x2c + 0x24), rd(bar0.base + 0x48), rd(bar0.base + 0x128));\n"
    + T + "}\n"
)
s = s[:end] + block + s[end:]
io.open(p, "w", encoding="utf-8").write(s)
print("apply-312 written")