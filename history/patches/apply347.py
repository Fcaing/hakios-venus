import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
old = "static uint32_t pcie_retrain;\t/* apply-331: do not poke the retrain bit by default */"
new = "static uint32_t pcie_retrain = 1;\t/* apply-347: poke the retrain bit by default, the endpoint refuses m0 without it */"
assert s.count(old) == 1
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-347 ok: pcie_retrain defaults to 1")