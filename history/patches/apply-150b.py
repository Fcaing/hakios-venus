p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(p).read()
old = "\t\tif (kr == KERN_SUCCESS && buffer != 0) {\n\t\t\tpcie_dma_pa = kvtophys(buffer);"
new = "\t\tif (kr == KERN_SUCCESS && buffer != 0) {\n\t\t\tpcie_dma = buffer;\n\t\t\tpcie_dma_pa = kvtophys(buffer);"
print("count", s.count(old))
assert s.count(old) == 1
s = s.replace(old, new)
open(p, "w").write(s)
print("patched")