P = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
src = open(P).read()
a = "\t\t\t\t\t\t\t\tif (pcie_resetpulse != 0) {"
assert src.count(a) == 1, src.count(a)
src = src.replace(a, "\t\t\t\t\t\t\t\tif (pcie_ee2m0 >= 2u) {\t/* apply-363b: pcie_ee2m0=2 also pulses RESET */")
open(P, "w").write(src)
print("apply-363b ok")
