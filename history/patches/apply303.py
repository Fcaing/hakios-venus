import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
old = "wr(pcie_dma_extra + o3 + 0x00, 1u | (2u << 8));"
assert s.count(old) == 1, s.count(old)
new = "wr(pcie_dma_extra + o3 + 0x00, 2u | (2u << 8));"
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-303 applied: chstate=RUNNING(2) | brstmode=DISABLE(2)")