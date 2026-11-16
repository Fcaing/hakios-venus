import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
a = "\t\t\t\t\t\t\t\t\twr(bar0.base + 0x700 + e3 * 8, (uint32_t)rb3);"
assert s.count(a) == 1
s = s.replace(a, "\t\t\t\t\t\t\t\t\twr(bar0.base + 0x700 + e3 * 8, (uint32_t)(rb3 + 0xff0));\n\t\t\t\t\t\t\t\t\tprintf(\"pcie: 5:   21: apply-287 er%u db <- 0x%08x (wp, not base)\\n\", e3, (uint32_t)(rb3 + 0xff0));")
io.open(p, "w", encoding="utf-8").write(s)
print("apply-287: er doorbell carries the wp")