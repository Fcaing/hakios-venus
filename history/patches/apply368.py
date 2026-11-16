P = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(P).read()

old_er = "\t\t\t\twr(bar0.base + 0x60, (uint32_t)(rctxt + 0x2000));\n"
old_er2 = "\t\t\t\twr(bar0.base + 0x64, (uint32_t)((rctxt + 0x2000) >> 32));\n"
old_cr = "\t\t\t\twr(bar0.base + 0x68, (uint32_t)(rctxt + 0x2400));\n"
old_cr2 = "\t\t\t\twr(bar0.base + 0x6c, (uint32_t)((rctxt + 0x2400) >> 32));\n"
for t in (old_er, old_er2, old_cr, old_cr2):
    assert s.count(t) == 1, (t, s.count(t))

s = s.replace(old_er, "\t\t\t\twr(bar0.base + 0x60, (uint32_t)(rctxt + 0x4000));\t/* apply-368: er at +0x4000 */\n")
s = s.replace(old_er2, "\t\t\t\twr(bar0.base + 0x64, (uint32_t)((rctxt + 0x4000) >> 32));\n")
s = s.replace(old_cr, "\t\t\t\twr(bar0.base + 0x68, (uint32_t)(rctxt + 0x7000));\t/* apply-368: cmd at +0x7000 */\n")
s = s.replace(old_cr2, "\t\t\t\twr(bar0.base + 0x6c, (uint32_t)((rctxt + 0x7000) >> 32));\n")
open(P, "w").write(s)
print("apply-368 ok")
