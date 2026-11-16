import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
anchor = 'printf("pcie: 5:   21: apply-286 m0 after mission: mh 0x%08x ee 0x%08x ctrl 0x%08x\\n",'
i = s.index(anchor)
j = s.index(");", i) + 2
T = "\t\t\t\t\t\t"
new = ("\n" + T + "/* apply-326: the device now sends a BW_REQ event on er2 (ring 0xa0206000).\n"
+ T + " * The vendor consumes it and answers on the bw scale doorbell:\n"
+ T + " * bw_scale_db = base + CHDBOFF + 8*126 = 0x6f0, value = (result<<8)|seq.\n"
+ T + " * Maybe the data engine waits for that answer.\n"
+ T + " */\n"
+ T + "{\n"
+ T + "\tuint32_t i26, rp26 = (uint32_t)(PCIE_EXTRA_IOVA + 0x6000);\n"
+ T + "\tuint32_t eb26 = (uint32_t)(PCIE_EXTRA_IOVA + 0x6000);\n"
+ T + "\tfor (i26 = 0; i26 < 200u; i26++) {\n"
+ T + "\t\t__asm__ volatile (\"dc ivac, %0\" : : \"r\" (pcie_dma_extra + 0x2000 + 2 * 0x2c + 0x1c) : \"memory\");\n"
+ T + "\t\trp26 = rd(pcie_dma_extra + 0x2000 + 2 * 0x2c + 0x1c);\n"
+ T + "\t\tif (rp26 != eb26) {\n"
+ T + "\t\t\tbreak;\n"
+ T + "\t\t}\n"
+ T + "\t\tsleep_ms(1);\n"
+ T + "\t}\n"
+ T + "\t{\n"
+ T + "\t\tuint32_t e0 = rd(pcie_dma_extra + 0x6000), e1 = rd(pcie_dma_extra + 0x6004);\n"
+ T + "\t\tuint32_t e2 = rd(pcie_dma_extra + 0x6008), e3 = rd(pcie_dma_extra + 0x600c);\n"
+ T + "\t\tuint32_t seq = e3 & 0xffu;\n"
+ T + "\t\tprintf(\"pcie: 5:   21: apply-326 bw req after %u ms rp 0x%08x ev %08x %08x %08x %08x seq %u\\n\",\n"
+ T + "\t\t    i26, rp26, e0, e1, e2, e3, seq);\n"
+ T + "\t\twr(bar0.base + 0x6f0u, (0u << 8) | seq);\n"
+ T + "\t\twr(pcie_dma_extra + 0x2000 + 2 * 0x2c + 0x1c, eb26 + 0x10u);\n"
+ T + "\t\t__asm__ volatile (\"dsb sy\" : : : \"memory\");\n"
+ T + "\t\twr(bar0.base + 0x700u + 2u * 8u, eb26 + 0x10u);\n"
+ T + "\t\tprintf(\"pcie: 5:   21: apply-326 bw ack seq %u, er2 rp -> 0x%08x, bwdb 0x%08x\\n\",\n"
+ T + "\t\t    seq, eb26 + 0x10u, rd(bar0.base + 0x6f0u));\n"
+ T + "\t}\n"
+ T + "}")
s = s[:j] + new + s[j:]
io.open(p, "w", encoding="utf-8").write(s)
print("apply-326 inserted")