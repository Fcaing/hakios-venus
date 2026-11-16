import io

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

idx = s.index("/* Leave the endpoint stream in place for the real transfer. */")
start = s.rindex("\n", 0, s.rindex("\n", 0, idx)) + 1
end = s.index("wr(smmu_cb + 0x58, fsr & PCIE_SMMU_FAULT);", idx)
end = s.index("}", end) + 1
end = s.index("}", end) + 1
end = s.index("\n", end) + 1
s = s[:start] + s[end:]

io.open(p, "w", encoding="utf-8").write(s)
print("apply-203 done")