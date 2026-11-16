import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
n0 = len(s)

for name, var in (("pcie_mhi_nobase", "pcie_mhi_nobase"),
                  ("pcie_mhi_nom0", "pcie_mhi_nom0"),
                  ("pcie_mhi_watch", "pcie_mhi_watch"),
                  ("pcie_headonly_pages", "pcie_headonly_pages"),
                  ("pcie_mhi_erdb", "pcie_mhi_erdb")):
    old = '\t\t\t\t\t\t\tPE_parse_boot_argn("%s", &want2, sizeof(want2));\n\t\t\t\t\t\t\t%s = want2;' % (name, var)
    new = '\t\t\t\t\t\t\twant2 = 0;\n\t\t\t\t\t\t\tif (PE_parse_boot_argn("%s", &want2, sizeof(want2))) {\n\t\t\t\t\t\t\t\t%s = want2;\n\t\t\t\t\t\t\t}' % (name, var)
    if s.count(old) == 1:
        s = s.replace(old, new)
        print("fixed", name)
    else:
        print("skip", name, s.count(old))

io.open(p, "w", encoding="utf-8").write(s)
print("ok", n0, "->", len(s))