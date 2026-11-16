import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

a1 = "wr(pcie_dma_extra + o3 + 0x14, (i3 == 1u) ? 0x1000u : 0x200u);   /* apply-324: DT sizes 0x20/0x100/0x20 */"
assert s.count(a1) == 1
s = s.replace(a1, "wr(pcie_dma_extra + o3 + 0x14, 0x1000u);   /* apply-325: back to one size, the DT sizes caused sys_err */")

a2 = "wr(pcie_dma_extra + o3 + 0x24, (uint32_t)(rb + ((i3 == 1u) ? 0xff0u : 0x1f0u)));"
assert s.count(a2) == 1
s = s.replace(a2, "wr(pcie_dma_extra + o3 + 0x24, (uint32_t)(rb + 0xff0u));")
io.open(p, "w", encoding="utf-8").write(s)
print("apply-325: er sizes reverted, bw scale kept")