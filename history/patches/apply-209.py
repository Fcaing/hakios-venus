import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
old = "\t\t\t\twr(bar0.base + 0x108, 0xa0000000u);"
new = ("\t\t\t\t/* apply-209: the BHI doorbell used 0xa0000000, which the SMMU does not\n"
       "\t\t\t\t * map (only 0xa0004000.. is in the page tables), so p204 got\n"
       "\t\t\t\t * FSR 0x80000402 on every fetch.  Point it at the mapped window. */\n"
       "\t\t\t\twr(bar0.base + 0x108, (uint32_t)PCIE_SMMU_IOVA);")
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("ok apply-209")