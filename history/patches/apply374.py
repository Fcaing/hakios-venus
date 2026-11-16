P = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(P).read()

a = "static uint32_t pcie_chrebuild;\t/* apply-373"
assert s.count(a) == 1
s = s.replace(a, "static uint32_t pcie_cmd_type = 1;\t/* apply-374: cmd ctxt word1 (0 vs 1 control) */\n" + a)

b = 'PE_parse_boot_argn("pcie_chrebuild", &pcie_chrebuild, sizeof(pcie_chrebuild));'
assert s.count(b) == 1
s = s.replace(b, b + '\n\tPE_parse_boot_argn("pcie_cmd_type", &pcie_cmd_type, sizeof(pcie_cmd_type));')

c = "\t\t\t\t\twr(pcie_dma_extra + 0x2400 + 0x04, 1u);\n"
assert s.count(c) == 1, s.count(c)
s = s.replace(c, "\t\t\t\t\twr(pcie_dma_extra + 0x2400 + 0x04, pcie_cmd_type);\n")
open(P, "w").write(s)
print("apply-374 ok")
