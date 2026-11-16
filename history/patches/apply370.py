P = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(P).read()

a = "static uint32_t pcie_rewrite;\t/* apply-367"
assert s.count(a) == 1
s = s.replace(a, "static uint32_t pcie_ch_ee;\t/* apply-370: set the ee field of the data chan contexts */\n" + a)

b = 'PE_parse_boot_argn("pcie_rewrite", &pcie_rewrite, sizeof(pcie_rewrite));'
assert s.count(b) == 1
s = s.replace(b, b + '\n\tPE_parse_boot_argn("pcie_ch_ee", &pcie_ch_ee, sizeof(pcie_ch_ee));')

anchor = "if (pcie_rewrite != 0) {"
assert s.count(anchor) == 1, s.count(anchor)
i = s.find(anchor)

block = (
    "if (pcie_ch_ee != 0) {\n"
    "\t\t\t\t\tuint32_t old20 = rd(pcie_dma_extra + 0x2000 + 20 * 0x2c + 0x08);\n"
    "\t\t\t\t\twr(pcie_dma_extra + 0x2000 + 20 * 0x2c + 0x08, pcie_ch_ee);\n"
    "\t\t\t\t\twr(pcie_dma_extra + 0x2000 + 21 * 0x2c + 0x08, pcie_ch_ee);\n"
    "\t\t\t\t\t__asm__ __volatile__(\"dc civac, %0\" :: \"r\"(pcie_dma_extra + 0x2000 + 20 * 0x2c) : \"memory\");\n"
    "\t\t\t\t\t__asm__ __volatile__(\"dc civac, %0\" :: \"r\"(pcie_dma_extra + 0x2000 + 21 * 0x2c) : \"memory\");\n"
    "\t\t\t\t\t__asm__ __volatile__(\"dsb sy\" ::: \"memory\");\n"
    "\t\t\t\t\twr(bar0.base + 0x300 + 20 * 8 + 4u, 0u);\n"
    "\t\t\t\t\twr(bar0.base + 0x300 + 20 * 8, (uint32_t)(PCIE_EXTRA_IOVA + 0xc020));\n"
    "\t\t\t\t\twr(bar0.base + 0x300 + 21 * 8 + 4u, 0u);\n"
    "\t\t\t\t\twr(bar0.base + 0x300 + 21 * 8, (uint32_t)(PCIE_EXTRA_IOVA + 0xd000));\n"
    "\t\t\t\t\tprintf(\"pcie: 5:   21: apply-370 ch ee %u -> %u: ch20 rp 0x%08x mh 0x%08x\\n\",\n"
    "\t\t\t\t\t       old20, rd(pcie_dma_extra + 0x2000 + 20 * 0x2c + 0x08),\n"
    "\t\t\t\t\t       rd(pcie_dma_extra + 0x2000 + 20 * 0x2c + 0x1c), rd(bar0.base + 0x3c));\n"
    "\t\t\t\t}\n"
)
s = s[:i] + block + s[i:]
open(P, "w").write(s)
print("apply-370 ok")
