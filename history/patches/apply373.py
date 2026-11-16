P = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(P).read()

a = "static uint32_t pcie_ch_word0 = 0xffffffff;\t/* apply-372"
assert s.count(a) == 1
s = s.replace(a, "static uint32_t pcie_chrebuild;\t/* apply-373: rebuild the data chan ctxt in mission */\n" + a)

b = 'PE_parse_boot_argn("pcie_ch_word0", &pcie_ch_word0, sizeof(pcie_ch_word0));'
assert s.count(b) == 1
s = s.replace(b, b + '\n\tPE_parse_boot_argn("pcie_chrebuild", &pcie_chrebuild, sizeof(pcie_chrebuild));')

outer = "if (pcie_ch_ee != 0) {"
assert s.count(outer) == 1
block = (
    "if (pcie_chrebuild != 0) {\n"
    "\t\t\t\t\tuint64_t rb20 = (uint64_t)PCIE_EXTRA_IOVA + 0xc000;\n"
    "\t\t\t\t\tuint64_t rb21 = (uint64_t)PCIE_EXTRA_IOVA + 0xd000;\n"
    "\t\t\t\t\tvolatile uint32_t *c20 = (volatile uint32_t *)(pcie_dma_extra + 0x2000 + 20 * 0x2c);\n"
    "\t\t\t\t\tvolatile uint32_t *c21 = (volatile uint32_t *)(pcie_dma_extra + 0x2000 + 21 * 0x2c);\n"
    "\t\t\t\t\tint ci;\n"
    "\t\t\t\t\tfor (ci = 0; ci < 11; ci++) { c20[ci] = 0; c21[ci] = 0; }\n"
    "\t\t\t\t\tc20[1] = 3u;\t/* out */\n"
    "\t\t\t\t\tc20[2] = 2u;\t/* ee 2 */\n"
    "\t\t\t\t\tc20[3] = (uint32_t)rb20; c20[4] = (uint32_t)(rb20 >> 32);\n"
    "\t\t\t\t\tc20[5] = 0x1000u; c20[6] = 0u;\n"
    "\t\t\t\t\tc20[7] = (uint32_t)rb20; c20[8] = (uint32_t)(rb20 >> 32);\n"
    "\t\t\t\t\tc20[9] = (uint32_t)(rb20 + 0x20); c20[10] = (uint32_t)((rb20 + 0x20) >> 32);\n"
    "\t\t\t\t\tc21[1] = 1u;\t/* in */\n"
    "\t\t\t\t\tc21[2] = 2u;\n"
    "\t\t\t\t\tc21[3] = (uint32_t)rb21; c21[4] = (uint32_t)(rb21 >> 32);\n"
    "\t\t\t\t\tc21[5] = 0x1000u; c21[6] = 0u;\n"
    "\t\t\t\t\tc21[7] = (uint32_t)rb21; c21[8] = (uint32_t)(rb21 >> 32);\n"
    "\t\t\t\t\tc21[9] = (uint32_t)(rb21 + 0x200); c21[10] = (uint32_t)((rb21 + 0x200) >> 32);\n"
    "\t\t\t\t\t__asm__ __volatile__(\"dc civac, %0\" :: \"r\"(pcie_dma_extra + 0x2000 + 20 * 0x2c) : \"memory\");\n"
    "\t\t\t\t\t__asm__ __volatile__(\"dc civac, %0\" :: \"r\"(pcie_dma_extra + 0x2000 + 21 * 0x2c) : \"memory\");\n"
    "\t\t\t\t\t__asm__ __volatile__(\"dsb sy\" ::: \"memory\");\n"
    "\t\t\t\t\twr(bar0.base + 0x300 + 20 * 8 + 4u, 0u);\n"
    "\t\t\t\t\twr(bar0.base + 0x300 + 20 * 8, (uint32_t)(rb20 + 0x20));\n"
    "\t\t\t\t\twr(bar0.base + 0x300 + 21 * 8 + 4u, 0u);\n"
    "\t\t\t\t\twr(bar0.base + 0x300 + 21 * 8, (uint32_t)(rb21 + 0x200));\n"
    "\t\t\t\t\tprintf(\"pcie: 5:   21: apply-373 rebuilt ch20/21: c20 %08x %08x %08x %08x c21 %08x %08x mh 0x%08x\\n\",\n"
    "\t\t\t\t\t       c20[0], c20[1], c20[2], c20[3], c21[1], c21[2], rd(bar0.base + 0x3c));\n"
    "\t\t\t\t}\n"
)
i = s.find(outer)
s = s[:i] + block + s[i:]
open(P, "w").write(s)
print("apply-373 ok")
