import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
old = """						pcie_note("mhi ready %u status 0x%08x ee 0x%08x; ",
						    k, rd(bar0.base + 0x48), rd(bar0.base + 0x128));
					}"""
assert s.count(old) == 1, s.count(old)
new = """						printf("pcie: 5:   21: after the wait: fsr 0x%08x gfsr 0x%08x far 0x%08x:%08x bhi 0x%08x ee 0x%08x errcode 0x%08x\\n",
						    rd(smmu_cb + 0x58), rd(smmu_mmio + 0x48),
						    rd(smmu_cb + 0x64), rd(smmu_cb + 0x60),
						    rd(bar0.base + 0x12c), rd(bar0.base + 0x128), rd(bar0.base + 0x130));
						pcie_note("mhi ready %u status 0x%08x ee 0x%08x; ",
						    k, rd(bar0.base + 0x48), rd(bar0.base + 0x128));
					}"""
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("ok apply-217")