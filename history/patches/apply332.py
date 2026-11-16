import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
assert "apply-332" not in s

a1 = "static uint32_t pcie_mhi_state_val = 2;"
assert s.count(a1) == 1
s = s.replace(a1, a1 + "\nstatic uint32_t pcie_rddm;\t/* apply-332: collect the firmware's crash dump */", 1)

a2 = "PE_parse_boot_argn(\"pcie_trap_buf\""
i = s.index(a2)
j = s.index("}", i) + 1
s = s[:j] + "\n\t\t\t\t\t\t\t{ uint32_t d33 = 0; if (PE_parse_boot_argn(\"pcie_rddm\", &d33, sizeof(d33))) { pcie_rddm = d33; } }" + s[j:]

a3 = "apply-251 after init: cfg 0x%08x ccbap 0x%08x ecbap 0x%08x"
k = s.index(a3)
k2 = s.index(";", k) + 1

T = "\t" * 9
block = "\n" + T + "/* apply-332: build the RDDM receive table the vendor does, provoke the\n" + T + " * error, then read back what the firmware dumped. */\n" + T + "if (pcie_rddm != 0) {\n" + \
 T + "\tuint64_t rtab = PCIE_EXTRA_IOVA + 0x620000ull;\n" + \
 T + "\tuint32_t rseg, rw, rnz, rst;\n" + \
 T + "\tfor (rseg = 0; rseg < 9u; rseg++) {\n" + \
 T + "\t\tuint64_t sa = PCIE_EXTRA_IOVA + 0x200000ull + (uint64_t)rseg * 0x80000ull;\n" + \
 T + "\t\tuint64_t sl = (rseg == 8u) ? 0x20000ull : 0x80000ull;\n" + \
 T + "\t\twr(pcie_dma_extra + 0x620000 + rseg * 16u + 0u, (uint32_t)sa);\n" + \
 T + "\t\twr(pcie_dma_extra + 0x620000 + rseg * 16u + 4u, (uint32_t)(sa >> 32));\n" + \
 T + "\t\twr(pcie_dma_extra + 0x620000 + rseg * 16u + 8u, (uint32_t)sl);\n" + \
 T + "\t\twr(pcie_dma_extra + 0x620000 + rseg * 16u + 12u, 0);\n" + \
 T + "\t}\n" + \
 T + "\twr(pcie_dma_extra + 0x620000 + 144u, (uint32_t)rtab);\n" + \
 T + "\twr(pcie_dma_extra + 0x620000 + 148u, (uint32_t)(rtab >> 32));\n" + \
 T + "\twr(pcie_dma_extra + 0x620000 + 152u, 160u);\n" + \
 T + "\twr(pcie_dma_extra + 0x620000 + 156u, 0);\n" + \
 T + "\tfor (rw = 0; rw < 0x1000; rw += 64) {\n" + \
 T + "\t\t__asm__ volatile (\"dc civac, %0\" : : \"r\" ((char *)(uintptr_t)(pcie_dma_extra + 0x620000 + rw)) : \"memory\");\n" + \
 T + "\t}\n" + \
 T + "\t__asm__ volatile (\"dsb sy\" : : : \"memory\");\n" + \
 T + "\twr(bar0.base + 0x224 + 0x64, (uint32_t)(rtab >> 32));\n" + \
 T + "\twr(bar0.base + 0x224 + 0x60, (uint32_t)rtab);\n" + \
 T + "\twr(bar0.base + 0x224 + 0x68, 160u);\n" + \
 T + "\twr(bar0.base + 0x224 + 0x70, 0x3320u);\n" + \
 T + "\tprintf(\"apply-332 rddm table 0x%llx rxvec %08x %08x %08x db %08x st %08x\\n\",\n" + \
 T + "\t    rtab, rd(bar0.base + 0x224 + 0x64), rd(bar0.base + 0x224 + 0x60),\n" + \
 T + "\t    rd(bar0.base + 0x224 + 0x68), rd(bar0.base + 0x224 + 0x70), rd(bar0.base + 0x224 + 0x78));\n" + \
 T + "\twr(bar0.base + 0x38, (rd(bar0.base + 0x38) & ~0xff00u) | (2u << 8));\n" + \
 T + "\tsleep_ms(400);\n" + \
 T + "\trst = rd(bar0.base + 0x224 + 0x78);\n" + \
 T + "\tprintf(\"apply-332 after the error: mh %08x ee %08x rxst %08x\\n\",\n" + \
 T + "\t    rd(bar0.base + 0x48), rd(bar0.base + 0x128), rst);\n" + \
 T + "\tfor (rw = 0; rw < 0x1000; rw += 64) {\n" + \
 T + "\t\t__asm__ volatile (\"dc ivac, %0\" : : \"r\" ((char *)(uintptr_t)(pcie_dma_extra + 0x200000 + rw)) : \"memory\");\n" + \
 T + "\t}\n" + \
 T + "\t__asm__ volatile (\"dsb sy\" : : : \"memory\");\n" + \
 T + "\trnz = 0;\n" + \
 T + "\tfor (rw = 0; rw < 0x4000u; rw++) {\n" + \
 T + "\t\tif (rd(pcie_dma_extra + 0x200000 + rw * 4u) != 0) {\n" + \
 T + "\t\t\trnz++;\n" + \
 T + "\t\t}\n" + \
 T + "\t}\n" + \
 T + "\tprintf(\"apply-332 seg0 nz %u of 16384, head\", rnz);\n" + \
 T + "\tfor (rw = 0; rw < 8u; rw++) {\n" + \
 T + "\t\tprintf(\" %08x\", rd(pcie_dma_extra + 0x200000 + rw * 4u));\n" + \
 T + "\t}\n" + \
 T + "\tprintf(\" ascii %.48s\\n\", (const char *)(uintptr_t)(pcie_dma_extra + 0x200000));\n" + \
 T + "}\n"
s = s[:k2] + block + s[k2:]
io.open(p, "w", encoding="utf-8").write(s)
print("ok", len(s))