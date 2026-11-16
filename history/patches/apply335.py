import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
assert "apply-335" not in s

a1 = "static uint32_t pcie_rddm;"
s = s.replace(a1, a1 + "\nstatic uint32_t pcie_qmi;\t/* apply-335: send a real qmi request as the first tre */", 1)

a2 = "PE_parse_boot_argn(\"pcie_rddm\""
i = s.index(a2)
j = s.index("}", i) + 1
s = s[:j] + "\n\t\t\t\t\t\t\t{ uint32_t d35 = 0; if (PE_parse_boot_argn(\"pcie_qmi\", &d35, sizeof(d35))) { pcie_qmi = d35; } }" + s[j:]

anchor = "\t\t\t\t\t\twr(bar0.base + 0x300 + dch * 8, (uint32_t)trewp);"
assert s.count(anchor) >= 1
T = "\t" * 6
block = (T + "/* apply-335: build the wlfw indication-register request the vendor sends\n"
         + T + " * first (qmi id 0x0020) and hand it over as the first data tre. */\n"
         + T + "if (pcie_qmi != 0) {\n"
         + T + "\tuint32_t qb = 0x800000u;\n"
         + T + "\tuint32_t qn, qt;\n"
         + T + "\tfor (qt = 0; qt < 128u; qt += 4u) {\n"
         + T + "\t\twr(pcie_dma_extra + qb + qt, 0u);\n"
         + T + "\t}\n"
         + T + "\tfor (qt = 0; qt < 11u; qt++) {\n"
         + T + "\t\twr(pcie_dma_extra + qb + 7u + qt * 4u, ((uint32_t)(qt + 1u) & 0xffu) | 0x00000100u);\n"
         + T + "\t}\n"
         + T + "\tqn = 7u + 11u * 4u;\n"
         + T + "\twr(pcie_dma_extra + qb + 0u, 0x00000000u);\n"
         + T + "\twr(pcie_dma_extra + qb + 1u, 0x00010000u);\n"
         + T + "\twr(pcie_dma_extra + qb + 4u, 0x00200000u | ((qn - 7u) << 16));\n"
         + T + "\tfor (qt = 0; qt < 256u; qt += 64) {\n"
         + T + "\t\t__asm__ volatile (\"dc civac, %0\" : : \"r\" ((char *)(uintptr_t)(pcie_dma_extra + qb + qt)) : \"memory\");\n"
         + T + "\t}\n"
         + T + "\t__asm__ volatile (\"dsb sy\" : : : \"memory\");\n"
         + T + "\twr(pcie_dma_extra + dring + 0x00u, (uint32_t)(PCIE_EXTRA_IOVA + qb));\n"
         + T + "\twr(pcie_dma_extra + dring + 0x04u, 0u);\n"
         + T + "\twr(pcie_dma_extra + dring + 0x08u, qn);\n"
         + T + "\twr(pcie_dma_extra + dring + 0x0cu, 0x00020200u);\n"
         + T + "\twr(pcie_dma_extra + dch * 0x2c + 0x24, (uint32_t)(dring + 0x10u));\n"
         + T + "\twr(pcie_dma_extra + dch * 0x2c + 0x28, (uint32_t)((dring + 0x10u) >> 32));\n"
         + T + "\ttrewp = dring + 0x10u;\n"
         + T + "\tprintf(\"apply-335 qmi req %u bytes at 0x%llx tre 0x%llx\\n\",\n"
         + T + "\t    qn, (unsigned long long)(PCIE_EXTRA_IOVA + qb), (unsigned long long)trewp);\n"
         + T + "}\n")
s = s.replace(anchor, block + anchor, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("ok")