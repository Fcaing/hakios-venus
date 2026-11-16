import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

# 1. declaration
decl = "static uint32_t pcie_mhi_nom0;\t/* apply-270: do not ask for m0, let the device do it */\n"
assert s.count(decl) == 1
s = s.replace(decl, decl + "static uint32_t pcie_rp_fix = 1;\t/* apply-338: put the read pointer back before the first tre */\n", 1)

# 2. parse
anchor = '\t\t\t\t\t\t\twant2 = 0;\n\t\t\t\t\t\t\tif (PE_parse_boot_argn("pcie_mhi_nom0", &want2, sizeof(want2))) {\n'
assert s.count(anchor) == 1
s = s.replace(anchor, anchor + '\t\t\t\t\t\t\twant2 = 0;\n\t\t\t\t\t\t\tif (PE_parse_boot_argn("pcie_rp_fix", &want2, sizeof(want2))) {\n\t\t\t\t\t\t\t\tpcie_rp_fix = want2;\n\t\t\t\t\t\t\t}\n', 1)

# 3. gate the two writes
old = ("\t\t\t\t\t\twr(pcie_dma_extra + dch * 0x2c + 0x1c, (uint32_t)(dring));\n"
       "\t\t\t\t\t\twr(pcie_dma_extra + dch * 0x2c + 0x20, 0u);\n"
       "\t\t\t\t\t\tprintf(\"pcie: 5:   21: apply-295 ch20 rp 0x%08x:%08x\\n\",\n"
       "\t\t\t\t\t\t    rd(pcie_dma_extra + dch * 0x2c + 0x20), rd(pcie_dma_extra + dch * 0x2c + 0x1c));\n")
assert s.count(old) == 1, s.count(old)
new = ("\t\t\t\t\t\tif (pcie_rp_fix != 0) {\n"
       "\t\t\t\t\t\t\twr(pcie_dma_extra + dch * 0x2c + 0x1c, (uint32_t)(dring));\n"
       "\t\t\t\t\t\t\twr(pcie_dma_extra + dch * 0x2c + 0x20, 0u);\n"
       "\t\t\t\t\t\t}\n"
       "\t\t\t\t\t\tprintf(\"pcie: 5:   21: apply-295 ch20 rp 0x%08x:%08x fix %u\\n\",\n"
       "\t\t\t\t\t\t    rd(pcie_dma_extra + dch * 0x2c + 0x20), rd(pcie_dma_extra + dch * 0x2c + 0x1c), pcie_rp_fix);\n")
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-338 applied")