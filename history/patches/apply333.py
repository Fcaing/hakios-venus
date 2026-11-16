import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
assert "apply-333" not in s
anchor = "T\tprintf(\"apply-332 seg0 nz %u of 16384, head\", rnz);"
T = "\t" * 9
anchor = T + "printf(\"apply-332 seg0 nz %u of 16384, head\", rnz);"
assert s.count(anchor) == 1
block = "\n" + T + "/* apply-333: walk the whole RDDM image and print the firmware's own\n" + T + " * log strings, which is the only way to see why it refuses the ring. */\n" + T + "{\n" + \
 T + "\tuint32_t sg2, of2, w2, n2, hits2;\n" + T + "\thits2 = 0;\n" + T + "\tfor (sg2 = 0; sg2 < 9u && hits2 < 16u; sg2++) {\n" + \
 T + "\t\tuint32_t lim2 = (sg2 == 8u) ? 0x8000u : 0x20000u;\n" + \
 T + "\t\tfor (of2 = 0; of2 < lim2; of2 += 4u) {\n" + \
 T + "\t\t\tchar b2[4];\n" + \
 T + "\t\t\tw2 = rd(pcie_dma_extra + 0x200000u + sg2 * 0x80000u + of2 * 4u);\n" + \
 T + "\t\t\tb2[0] = (char)(w2 & 0xff); b2[1] = (char)((w2 >> 8) & 0xff);\n" + \
 T + "\t\t\tb2[2] = (char)((w2 >> 16) & 0xff); b2[3] = (char)((w2 >> 24) & 0xff);\n" + \
 T + "\t\t\tif (b2[0] < 0x20 || b2[0] > 0x7e || b2[1] < 0x20 || b2[1] > 0x7e ||\n" + \
 T + "\t\t\t    b2[2] < 0x20 || b2[2] > 0x7e || b2[3] < 0x20 || b2[3] > 0x7e) {\n" + \
 T + "\t\t\t\tcontinue;\n" + T + "\t\t\t}\n" + \
 T + "\t\t\tif (of2 == 0u || rd(pcie_dma_extra + 0x200000u + sg2 * 0x80000u + (of2 - 4u) * 4u + 0u) == 0) {\n" + \
 T + "\t\t\t\t/* cheap start test: previous word not printable as a whole */\n" + \
 T + "\t\t\t}\n" + \
 T + "\t\t\tn2 = (uint32_t)((w2 & 0xff) | ((w2 >> 8) & 0xff00) | ((w2 & 0xff0000u) >> 0) | 0);\n" + \
 T + "\t\t\t(void)n2;\n" + \
 T + "\t\t\t{\n" + \
 T + "\t\t\t\tchar run2[48];\n" + T + "\t\t\t\tuint32_t k2 = 0, oo2 = of2, ww2;\n" + \
 T + "\t\t\t\twhile (k2 < 44u && oo2 < lim2 && k2 < 44u) {\n" + \
 T + "\t\t\t\t\tchar c2[4]; uint32_t q2, z2;\n" + \
 T + "\t\t\t\t\tww2 = rd(pcie_dma_extra + 0x200000u + sg2 * 0x80000u + oo2 * 4u);\n" + \
 T + "\t\t\t\t\tc2[0] = (char)(ww2 & 0xff); c2[1] = (char)((ww2 >> 8) & 0xff);\n" + \
 T + "\t\t\t\t\tc2[2] = (char)((ww2 >> 16) & 0xff); c2[3] = (char)((ww2 >> 24) & 0xff);\n" + \
 T + "\t\t\t\t\tfor (z2 = 0; z2 < 4u; z2++) {\n" + \
 T + "\t\t\t\t\t\tif (c2[z2] < 0x20 || c2[z2] > 0x7e) { break; }\n" + \
 T + "\t\t\t\t\t\trun2[k2++] = c2[z2];\n" + \
 T + "\t\t\t\t\t}\n" + \
 T + "\t\t\t\t\tif (z2 < 4u) { break; }\n" + \
 T + "\t\t\t\t\too2++;\n" + \
 T + "\t\t\t\t}\n" + \
 T + "\t\t\t\trun2[k2] = 0;\n" + \
 T + "\t\t\t\tif (k2 >= 8u) {\n" + \
 T + "\t\t\t\t\tconst char *q3 = run2;\n" + \
 T + "\t\t\t\t\tuint32_t ok3 = 0;\n" + \
 T + "\t\t\t\t\twhile (*q3 && !ok3) {\n" + \
 T + "\t\t\t\t\t\tif ((q3[0] == 'm' || q3[0] == 'M') && (q3[1] == 'H' || q3[1] == 'h') && (q3[2] == 'I' || q3[2] == 'i')) { ok3 = 1; }\n" + \
 T + "\t\t\t\t\t\tif (q3[0] == 'a' && q3[1] == 's' && q3[2] == 's' && q3[3] == 'e') { ok3 = 1; }\n" + \
 T + "\t\t\t\t\t\tif (q3[0] == 't' && q3[1] == 'i' && q3[2] == 'm' && q3[3] == 'e') { ok3 = 1; }\n" + \
 T + "\t\t\t\t\t\tq3++;\n" + \
 T + "\t\t\t\t\t\t(void)q2_unused;\n" + \
 T + "\t\t\t\t\t}\n" + \
 T + "\t\t\t\t\tif (ok3) {\n" + \
 T + "\t\t\t\t\t\tprintf(\"apply-333 s%u+%05x %s\\n\", sg2, of2 * 4u, run2);\n" + \
 T + "\t\t\t\t\t\thits2++;\n" + \
 T + "\t\t\t\t\t\tif (hits2 >= 16u) { break; }\n" + \
 T + "\t\t\t\t\t\tof2 += k2;\n" + \
 T + "\t\t\t\t\t}\n" + \
 T + "\t\t\t\t}\n" + \
 T + "\t\t\t}\n" + \
 T + "\t\t}\n" + \
 T + "\t}\n" + \
 T + "\tprintf(\"apply-333 hits %u\\n\", hits2);\n" + \
 T + "}\n"
# remove the bogus q2_unused line
block = block.replace(T + "\t\t\t\t\t\t(void)q2_unused;\n", "")
s = s.replace(anchor, anchor + block, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("ok", len(s))