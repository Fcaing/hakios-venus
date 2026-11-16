P = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
src = open(P).read()
a = '\tPE_parse_boot_argn("pcie_noearlystate", &pcie_noearlystate, sizeof(pcie_noearlystate));\n'
assert src.count(a) == 1, src.count(a)
src = src.replace(a, a + '\tif (pcie_noearlystate != 0) {\n\t\tprintf("pcie: apply-361 no MHICTRL writes before ee 2\\n");\n\t}\n')
open(P, "w").write(src)
print("apply-361b ok")
