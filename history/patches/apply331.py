import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
if "pcie_retrain" not in s:
    a = "static uint32_t pcie_gen = 1;\t/* apply-330: target link speed, 1 = gen1, 2 = gen2 */"
    assert s.count(a) == 1
    s = s.replace(a, a + "\nstatic uint32_t pcie_retrain;\t/* apply-331: do not poke the retrain bit by default */")
old = "\tif (pcie_gen > 1u) {\n"
new = "\t{\n\t\tuint32_t rt = pcie_retrain;\n\n\t\tif (PE_parse_boot_argn(\"pcie_retrain\", &rt, sizeof(rt))) {\n\t\t\tpcie_retrain = rt;\n\t\t}\n\t}\n\tif (pcie_gen > 1u && pcie_retrain != 0) {\n"
assert s.count(old) >= 1
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-331 ok")