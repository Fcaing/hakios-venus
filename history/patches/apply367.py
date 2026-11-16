P = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
src = open(P).read()

# declare + parse
a = "static uint32_t pcie_mission;\t/* apply-355"
assert src.count(a) == 1
src = src.replace(a, "static uint32_t pcie_rewrite;\t/* apply-367: rewrite the mhi bases after m0 */\n" + a)

b = 'PE_parse_boot_argn("pcie_erfull", &pcie_erfull, sizeof(pcie_erfull));\t/* apply-366 */'
assert src.count(b) == 1
src = src.replace(b, b + '\n\tPE_parse_boot_argn("pcie_rewrite", &pcie_rewrite, sizeof(pcie_rewrite));')

# insert the rewrite just before the data TRE is built
anchor = 'printf("pcie: 5:   21: apply-292 send:'
i = src.rfind(anchor)
assert i > 0
line_start = src.rfind("\n", 0, i) + 1
indent = src[line_start:i]

block = (
    'if (pcie_rewrite != 0) {\n'
    + indent + '\tuint64_t rctxt = (uint64_t)PCIE_EXTRA_IOVA;\n'
    + indent + '\tuint32_t rcfg;\n'
    + indent + '\twr(bar0.base + 0x58, (uint32_t)rctxt);\n'
    + indent + '\twr(bar0.base + 0x5c, (uint32_t)(rctxt >> 32));\n'
    + indent + '\twr(bar0.base + 0x60, (uint32_t)(rctxt + 0x2000));\n'
    + indent + '\twr(bar0.base + 0x64, (uint32_t)((rctxt + 0x2000) >> 32));\n'
    + indent + '\twr(bar0.base + 0x68, (uint32_t)(rctxt + 0x2400));\n'
    + indent + '\twr(bar0.base + 0x6c, (uint32_t)((rctxt + 0x2400) >> 32));\n'
    + indent + '\trcfg = rd(bar0.base + 0x10);\n'
    + indent + '\twr(bar0.base + 0x10, (rcfg & 0xffffu) | (3u << 16));\n'
    + indent + '\tdsb sy();\n'
    + indent + '\tprintf("pcie: 5:   21: apply-367 bases rewritten: cfg 0x%08x -> 0x%08x ccabap 0x%08x:%08x crcbap 0x%08x:%08x mh 0x%08x\\n",\n'
    + indent + '\t       rcfg, rd(bar0.base + 0x10), rd(bar0.base + 0x5c), rd(bar0.base + 0x58),\n'
    + indent + '\t       rd(bar0.base + 0x6c), rd(bar0.base + 0x68), rd(bar0.base + 0x3c));\n'
    + indent + '}\n'
)
src = src[:line_start] + block + src[line_start:]
open(P, "w").write(src)
print("apply-367 ok")
