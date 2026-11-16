import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
old = "if (pcie_chanstart2 != 0 && smmu_state == 1 && pcie_dma_extra != 0) {"
assert s.count(old) == 1
s = s.replace(old, "if (smmu_state == 1 && pcie_dma_extra != 0) {")
io.open(p, "w", encoding="utf-8").write(s)
print("apply-283: channel start is unconditional now")