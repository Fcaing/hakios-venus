import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

def probe(tag):
    return ('\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-350 %s: mh 0x%%08x ee 0x%%08x ctrl 0x%%08x cfg 0x%%08x\\n",\n'
            '\t\t\t\t\t\t\t    rd(bar0.base + 0x48), rd(bar0.base + 0x128),\n'
            '\t\t\t\t\t\t\t    rd(bar0.base + 0x38), rd(bar0.base + 0x10));\n') % tag

a1 = "\t\t\t\t\t\t\twr(bar0.base + 0x68, (uint32_t)crct);\n"
assert s.count(a1) >= 1
# insert only at the occurrence inside the apply-251 block (the one followed later by apply-264 after m0)
idx = s.rfind(a1)
s = s[:idx+len(a1)] + probe("a bases") + s[idx+len(a1):]

a2 = "\t\t\t\t\t\t\tif (pcie_mhi_erdb != 0) {\n"
assert s.count(a2) == 1
s = s.replace(a2, probe("b cfg") + a2)

a3 = "\t\t\t\t\t\t\tif (pcie_mhi_nom0 == 0 && pcie_mhi_m0late == 0) {\n"
assert s.count(a3) == 1
s = s.replace(a3, probe("c erdb") + a3)

io.open(p, "w", encoding="utf-8").write(s)
print("apply-350 ok")