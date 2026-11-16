P = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(P).read()

a = "static uint32_t pcie_dtbch;\t/* apply-375"
assert s.count(a) == 1
s = s.replace(a, "static uint32_t pcie_img512;\t/* apply-376: force BHI IMGSIZE to 0x80000 like the real device */\n" + a)

b = 'PE_parse_boot_argn("pcie_dtbch", &pcie_dtbch, sizeof(pcie_dtbch));'
assert s.count(b) == 1
s = s.replace(b, b + '\n\tPE_parse_boot_argn("pcie_img512", &pcie_img512, sizeof(pcie_img512));')

c = "\t\t\t\twr(bar0.base + 0x118, db);\n"
assert s.count(c) == 1, s.count(c)
ins = ("\t\t\t\tif (pcie_img512 != 0) {\n"
       "\t\t\t\t\tprintf(\"pcie: 5:   21: apply-376 imgsize was 0x%08x, forcing 0x80000\\n\", rd(bar0.base + 0x110));\n"
       "\t\t\t\t\twr(bar0.base + 0x110, 0x00080000u);\n"
       "\t\t\t\t}\n") + c
s = s.replace(c, ins)
open(P, "w").write(s)
print("apply-376 ok")
