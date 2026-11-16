import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
T = "\t" * 6
anchor = T + 'printf("pcie: 5:   21: apply-293 final rp 0x%08x wp 0x%08x'
assert s.count(anchor) == 1, s.count(anchor)
new = (T + "/* apply-294: dump the ch20 context, word by word */\n"
       + T + "for (d6 = 0x340; d6 < 0x420; d6 += 64) {\n"
       + T + "\t__asm__ volatile (\"dc ivac, %0\" : : \"r\" (pcie_dma_extra + d6) : \"memory\");\n"
       + T + "}\n"
       + T + "for (d6 = 0; d6 < 3; d6++) {\n"
       + T + "\te5 = (volatile uint32_t *)(pcie_dma_extra + 20 * 0x2c + d6 * 0x10);\n"
       + T + "\tprintf(\"pcie: 5:   21: apply-294 ch20[%02x] %08x %08x %08x %08x\\n\", d6 * 0x10, e5[0], e5[1], e5[2], e5[3]);\n"
       + T + "}\n"
       + T + "e5 = (volatile uint32_t *)(pcie_dma_extra + 20 * 0x2c + 0x2c - 0x10);\n"
       + T + "printf(\"pcie: 5:   21: apply-294 ch20 tail %08x %08x %08x %08x\\n\", e5[0], e5[1], e5[2], e5[3]);\n\n")
s = s.replace(anchor, new + anchor)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-294 in", len(s))