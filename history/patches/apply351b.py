import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
T = "\t" * 7
old = (
T + 'want2 = 0;\n' +
T + 'if (PE_parse_boot_argn("pcie_mhi_nom0", &want2, sizeof(want2))) {\n' +
T + 'want2 = 0;\n' +
T + 'if (PE_parse_boot_argn("pcie_rp_fix", &want2, sizeof(want2))) {\n' +
T + 'want2 = 0;\n' +
T + 'if (PE_parse_boot_argn("pcie_m0_delay", &want2, sizeof(want2))) {\n' +
T + '\tpcie_m0_delay = want2;\n' +
T + '}\n' +
T + '\tpcie_rp_fix = want2;\n' +
T + '}\n' +
T + '\tpcie_mhi_nom0 = want2;\n' +
T + '}\n')
new = (
T + 'want2 = 0;\n' +
T + 'if (PE_parse_boot_argn("pcie_mhi_nom0", &want2, sizeof(want2))) {\n' +
T + '\tpcie_mhi_nom0 = want2;\t/* apply-351: the old nest zeroed want2 again, so nom0 always read 0 */\n' +
T + '}\n' +
T + 'want2 = 0;\n' +
T + 'if (PE_parse_boot_argn("pcie_rp_fix", &want2, sizeof(want2))) {\n' +
T + '\tpcie_rp_fix = want2;\n' +
T + '}\n' +
T + 'want2 = 0;\n' +
T + 'if (PE_parse_boot_argn("pcie_m0_delay", &want2, sizeof(want2))) {\n' +
T + '\tpcie_m0_delay = want2;\n' +
T + '}\n')
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-351 ok")