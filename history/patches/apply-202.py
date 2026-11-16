import io, re

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

# 1) drop the MHI reset pulse: it restarts the BHI state machine right
#    before we ring, and every run that had it failed.
start = s.index("/*\n\t\t\t\t * apply-182: p183 proved")
end = s.index('rd(bar0.base + 0x38), rd(bar0.base + 0x48));\n\t\t\t\t}', start)
end = s.index("}", s.index(";", end)) + 1
s = s[:start] + s[end:]

# 2) drop the guard test: it rings the doorbell with a bad address first,
#    and p198 showed ERRDBG1 never moved off that address afterwards.
start = s.index("/*\n\t\t\t\t * apply-178: star's dma_fault_probe")
end = s.index("wr(smmu_cb + 0x58, fsr & PCIE_SMMU_FAULT);\n\t\t\t\t}", start)
end = s.index("}", s.index(";", end)) + 1
s = s[:start] + s[end:]

io.open(p, "w", encoding="utf-8").write(s)
print("apply-202 done")