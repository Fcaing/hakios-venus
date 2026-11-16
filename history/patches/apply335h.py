import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
assert "apply-335 a:" not in s
anchor = "\t\t\t\t\t\twr(bar0.base + 0x300 + dch * 8, (uint32_t)trewp);"
assert s.count(anchor) >= 1
T = "\t" * 6
P = T + "\t"
block = (T + "if (pcie_mhi_data != 0 && smmu_state == 1) {\n"
       + P + "volatile uint8_t *qp = (volatile uint8_t *)(uintptr_t)(pcie_dma_extra + 0xe000u);\n"
       + P + "uint32_t qn = 51u, qt;\n"
       + P + "printf(\"apply-335 a: va 0x%llx first %08x\\n\", (unsigned long long)(uintptr_t)qp, rd(pcie_dma_extra + 0xe000u));\n"
       + P + "for (qt = 0; qt < 64u; qt++) { qp[qt] = 0; }\n"
       + P + "printf(\"apply-335 b: zeroed, word0 %08x\\n\", rd(pcie_dma_extra + 0xe000u));\n"
       + P + "qp[1] = 1; qp[3] = 0x20; qp[5] = (uint8_t)(qn - 7u);\n"
       + P + "for (qt = 0; qt < 11u; qt++) {\n"
       + P + "\tqp[7u + qt * 4u] = (uint8_t)(qt + 1u);\n"
       + P + "\tqp[8u + qt * 4u] = 1u;\n"
       + P + "\tqp[9u + qt * 4u] = 0u;\n"
       + P + "\tqp[10u + qt * 4u] = 1u;\n"
       + P + "}\n"
       + P + "printf(\"apply-335 c: filled, words %08x %08x %08x\\n\", rd(pcie_dma_extra + 0xe000u), rd(pcie_dma_extra + 0xe004u), rd(pcie_dma_extra + 0xe008u));\n"
       + P + "__asm__ volatile (\"dsb sy\" : : : \"memory\");\n"
       + P + "for (qt = 0; qt < 128u; qt += 64) {\n"
       + P + "\t__asm__ volatile (\"dc civac, %0\" : : \"r\" ((char *)(uintptr_t)(pcie_dma_extra + 0xe000u + qt)) : \"memory\");\n"
       + P + "}\n"
       + P + "__asm__ volatile (\"dsb sy\" : : : \"memory\");\n"
       + P + "printf(\"apply-335 d: flushed\\n\");\n"
       + P + "wr(pcie_dma_extra + dring + 0x08u, qn);\n"
       + P + "printf(\"apply-335 e: tre len %u\\n\", rd(pcie_dma_extra + dring + 0x08u));\n"
       + P + "}\n")
s = s.replace(anchor, block + anchor, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("instrumented block added")