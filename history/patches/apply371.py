P = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(P).read()

a = "static uint32_t pcie_ch_ee;\t/* apply-370"
assert s.count(a) == 1
s = s.replace(a, "static uint32_t pcie_ch_type;\t/* apply-371: chan ctxt type (dir << 1 | 1) */\n" + a)

b = 'PE_parse_boot_argn("pcie_ch_ee", &pcie_ch_ee, sizeof(pcie_ch_ee));'
assert s.count(b) == 1
s = s.replace(b, b + '\n\tPE_parse_boot_argn("pcie_ch_type", &pcie_ch_type, sizeof(pcie_ch_type));')

anchor = "\t\t\t\t\tprintf(\"pcie: 5:   21: apply-370 ch ee %u -> %u: ch20 rp 0x%08x mh 0x%08x\\n\","
assert s.count(anchor) == 1
block = (
    "\t\t\t\t\tif (pcie_ch_type != 0) {\n"
    "\t\t\t\t\t\tuint32_t t21 = (pcie_ch_type == 3u) ? 1u : 3u;\n"
    "\t\t\t\t\t\twr(pcie_dma_extra + 0x2000 + 20 * 0x2c + 0x04, pcie_ch_type);\n"
    "\t\t\t\t\t\twr(pcie_dma_extra + 0x2000 + 21 * 0x2c + 0x04, t21);\n"
    "\t\t\t\t\t\t__asm__ __volatile__(\"dc civac, %0\" :: \"r\"(pcie_dma_extra + 0x2000 + 20 * 0x2c) : \"memory\");\n"
    "\t\t\t\t\t\t__asm__ __volatile__(\"dc civac, %0\" :: \"r\"(pcie_dma_extra + 0x2000 + 21 * 0x2c) : \"memory\");\n"
    "\t\t\t\t\t\t__asm__ __volatile__(\"dsb sy\" ::: \"memory\");\n"
    "\t\t\t\t\t\twr(bar0.base + 0x300 + 20 * 8 + 4u, 0u);\n"
    "\t\t\t\t\t\twr(bar0.base + 0x300 + 20 * 8, (uint32_t)(PCIE_EXTRA_IOVA + 0xc020));\n"
    "\t\t\t\t\t\twr(bar0.base + 0x300 + 21 * 8 + 4u, 0u);\n"
    "\t\t\t\t\t\twr(bar0.base + 0x300 + 21 * 8, (uint32_t)(PCIE_EXTRA_IOVA + 0xd000));\n"
    "\t\t\t\t\t\tprintf(\"pcie: 5:   21: apply-371 ch type %u/%u: ch20 rp 0x%08x ch21 rp 0x%08x mh 0x%08x\\n\",\n"
    "\t\t\t\t\t\t       rd(pcie_dma_extra + 0x2000 + 20 * 0x2c + 0x04), rd(pcie_dma_extra + 0x2000 + 21 * 0x2c + 0x04),\n"
    "\t\t\t\t\t\t       rd(pcie_dma_extra + 0x2000 + 20 * 0x2c + 0x1c), rd(pcie_dma_extra + 0x2000 + 21 * 0x2c + 0x1c),\n"
    "\t\t\t\t\t\t       rd(bar0.base + 0x3c));\n"
    "\t\t\t\t\t}\n"
)
i = s.find(anchor)
s = s[:i] + block + s[i:]
open(P, "w").write(s)
print("apply-371 ok")
