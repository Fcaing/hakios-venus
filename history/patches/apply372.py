P = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(P).read()

a = "static uint32_t pcie_ch_type;\t/* apply-371"
assert s.count(a) == 1
s = s.replace(a, "static uint32_t pcie_ch_word0 = 0xffffffff;\t/* apply-372: ch ctxt word0 */\n" + a)

b = 'PE_parse_boot_argn("pcie_ch_type", &pcie_ch_type, sizeof(pcie_ch_type));'
assert s.count(b) == 1
s = s.replace(b, b + '\n\tPE_parse_boot_argn("pcie_ch_word0", &pcie_ch_word0, sizeof(pcie_ch_word0));')

anchor = "\t\t\t\t\tif (pcie_ch_type != 0) {\n"
assert s.count(anchor) == 1
block = (
    "\t\t\t\t\tif (pcie_ch_word0 != 0xffffffffu) {\n"
    "\t\t\t\t\t\twr(pcie_dma_extra + 0x2000 + 20 * 0x2c + 0x00, pcie_ch_word0);\n"
    "\t\t\t\t\t\twr(pcie_dma_extra + 0x2000 + 21 * 0x2c + 0x00, pcie_ch_word0);\n"
    "\t\t\t\t\t\t__asm__ __volatile__(\"dc civac, %0\" :: \"r\"(pcie_dma_extra + 0x2000 + 20 * 0x2c) : \"memory\");\n"
    "\t\t\t\t\t\t__asm__ __volatile__(\"dc civac, %0\" :: \"r\"(pcie_dma_extra + 0x2000 + 21 * 0x2c) : \"memory\");\n"
    "\t\t\t\t\t\t__asm__ __volatile__(\"dsb sy\" ::: \"memory\");\n"
    "\t\t\t\t\t\tprintf(\"pcie: 5:   21: apply-372 word0 %u: ch20 0x%08x ch21 0x%08x\\n\",\n"
    "\t\t\t\t\t\t       pcie_ch_word0, rd(pcie_dma_extra + 0x2000 + 20 * 0x2c),\n"
    "\t\t\t\t\t\t       rd(pcie_dma_extra + 0x2000 + 21 * 0x2c));\n"
    "\t\t\t\t\t\twr(bar0.base + 0x300 + 20 * 8 + 4u, 0u);\n"
    "\t\t\t\t\t\twr(bar0.base + 0x300 + 20 * 8, (uint32_t)(PCIE_EXTRA_IOVA + 0xc020));\n"
    "\t\t\t\t\t\twr(bar0.base + 0x300 + 21 * 8 + 4u, 0u);\n"
    "\t\t\t\t\t\twr(bar0.base + 0x300 + 21 * 8, (uint32_t)(PCIE_EXTRA_IOVA + 0xd000));\n"
    "\t\t\t\t\t}\n"
)
i = s.find(anchor)
s = s[:i] + block + s[i:]
open(P, "w").write(s)
print("apply-372 ok")
