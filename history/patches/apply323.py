import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

anchor = 'printf("pcie: 5:   21: apply-269 wake db 0x%08x = 0x%08x\\n",'
i = s.index(anchor)
# find the end of that printf statement: the next line containing ');' after i
j = s.index(");", i) + 2

T = "\t\t\t\t\t\t"
new = (
"\n" + T + "/* apply-323: walk the MHI capability list.  MISC(0x24) holds the offset of\n"
+ T + " * the first capability; each capability word has id in 31:24 and the offset\n"
+ T + " * of the next one in 23:12.  venus may advertise TIMESYNC(2) and BW_SCALE(3),\n"
+ T + " * both of which the vendor writes a config register for and we never have.\n"
+ T + " */\n"
+ T + "{\n"
+ T + "\tuint32_t c23 = rd(bar0.base + 0x24u);\n"
+ T + "\tuint32_t k23, w23;\n"
+ T + "\tprintf(\"pcie: 5:   21: apply-323 misc 0x%08x first cap 0x%x\\n\", c23, c23 & 0xffffu);\n"
+ T + "\tfor (k23 = 0; k23 < 8u && (c23 & 0xffffu) < 0x1000u && (c23 & 0xffffu) != 0u; k23++) {\n"
+ T + "\t\tw23 = rd(bar0.base + (c23 & 0xffffu));\n"
+ T + "\t\tprintf(\"pcie: 5:   21: apply-323 cap[%u] at 0x%x word 0x%08x id %u next 0x%x cfg4 0x%08x\\n\",\n"
+ T + "\t\t    k23, c23 & 0xffffu, w23, (w23 >> 24) & 0xffu, (w23 >> 12) & 0xfffu,\n"
+ T + "\t\t    rd(bar0.base + (c23 & 0xffffu) + 4u));\n"
+ T + "\t\tif (((w23 >> 12) & 0xfffu) == 0u) {\n"
+ T + "\t\t\tbreak;\n"
+ T + "\t\t}\n"
+ T + "\t\tc23 = (w23 >> 12) & 0xfffu;\n"
+ T + "\t}\n"
+ T + "}"
)
s = s[:j] + new + s[j:]
io.open(p, "w", encoding="utf-8").write(s)
print("apply-323 inserted")