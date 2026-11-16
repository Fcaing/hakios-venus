import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

a1 = "wr(pcie_dma_extra + o3 + 0x14, 0x1000u);"
assert s.count(a1) == 2, s.count(a1)
# only the one inside the er loop (the first occurrence) gets the per-ring length
i = s.index(a1)
s = s[:i] + "wr(pcie_dma_extra + o3 + 0x14, (i3 == 1u) ? 0x1000u : 0x200u);   /* apply-324: DT sizes 0x20/0x100/0x20 */" + s[i+len(a1):]

a2 = "wr(pcie_dma_extra + o3 + 0x24, (uint32_t)(rb + 0xff0u));"
assert s.count(a2) == 1
s = s.replace(a2, "wr(pcie_dma_extra + o3 + 0x24, (uint32_t)(rb + ((i3 == 1u) ? 0xff0u : 0x1f0u)));")

a3 = "\t\t\t\t\t\t\t\to3 = 0x2400;"
assert s.count(a3) == 1
T = "\t\t\t\t\t\t\t\t"
new = (T + "/* apply-324: venus advertises exactly one MHI capability, BW_SCALE at 0x%x.\n"
+ T + " * The vendor's mhi_init_bw_scale() writes BW_SCALE_CFG there with the ER that\n"
+ T + " * carries BW_REQ events -- the DT says event ring 2 (data-type 3).\n"
+ T + " * Without it the device never asks the host to change link speed/width.\n"
+ T + " */\n"
+ T + "wr(bar0.base + 0xa24u, 0xFD100000u);\n"
+ T + "printf(\"pcie: 5:   21: apply-324 bw scale adv 0x%08x -> 0x%08x (er 2)\\n\",\n"
+ T + "    0u, rd(bar0.base + 0xa24u));\n"
+ T + "o3 = 0x2400;")
s = s.replace(a3, new)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-324 applied")