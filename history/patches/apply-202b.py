import io

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

# 1) drop the MHI reset pulse (keep the ctrl/stat read and its printf).
idx = s.index("apply-182: p183 proved")
start = s.rindex("/*", 0, idx)
end = s.index('rd(bar0.base + 0x38), rd(bar0.base + 0x48));', idx)
end = s.index("\n", end) + 1
s = s[:start] + s[end:]

# 2) drop the guard test: it rings the doorbell with a bad address first,
#    and p198 showed ERRDBG1 never moved off that address afterwards.
idx = s.index("apply-178: star's dma_fault_probe")
start = s.rindex("/*", 0, idx)
end = s.index("wr(smmu_cb + 0x58, fsr & PCIE_SMMU_FAULT);", idx)
end = s.index("\n", end) + 1
end = s.index("}", end) + 1
s = s[:start] + s[end:]

io.open(p, "w", encoding="utf-8").write(s)
print("apply-202 done")