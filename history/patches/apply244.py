import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
start = "\tif ((pcie_star_mask & 4u) && need(&tlmm)) {"
end = "\t\t       rd(gcc.base + 0x6b000), rd(gcc.base + 0x6c01c));\n\t}\n"
assert s.count(start) == 1, s.count(start)
i = s.index(start)
j = s.index(end, i) + len(end)
block = s[i:j]
s = s[:i] + s[j:]
anchor = "\t/* the PARF side, as pci-msm.c does before the PHY (msm_pcie_enable) */"
assert s.count(anchor) == 1
block = block.replace("star stage 5:", "star stage 5 (before parf, as star does):")
s = s.replace(anchor, block + "\n" + anchor)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-244 moved stage 5 before parf")