import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
assert "pcie_power_cycle" not in s
old = "static uint32_t pcie_reset;\t/* pcie_reset=1:"
assert s.count(old) == 1
s = s.replace(old, "static uint32_t pcie_power_cycle;\t/* pcie_power_cycle=1: collapse the domain before powering it up again */\nstatic uint32_t pcie_reset;\t/* pcie_reset=1:", 1)
old_size = "static uint32_t pcie_only, pcie_pause_ms = 300, pcie_fine, pcie_watch_seconds = 20, pcie_return;"
assert s.count(old_size) == 1
s = s.replace(old_size, "static uint32_t pcie_only, pcie_pause_ms = 300, pcie_fine, pcie_watch_seconds = 20, pcie_return, pcie_power_cycle;", 1)
anchor = "\t/* level 5: the power domain itself */\n"
assert s.count(anchor) == 1
cycle = anchor + """\tif (pcie_power_cycle) {
\t\tuint32_t now = rd(gcc.base + GCC_GDSCR);
\t\tprintf("pcie: 2:   power cycle: GDSCR 0x%08x -> set bit 0, the domain is collapsed\\n", now);
\t\twr(gcc.base + GCC_GDSCR, now | GDSC_SW_COLLAPSE);
\t\tsleep_ms(20);
\t\tprintf("pcie: 2:   power cycle: collapsed, GDSCR 0x%08x\\n", rd(gcc.base + GCC_GDSCR));
\t}
"""
s = s.replace(anchor, cycle, 1)
parse_anchor = "\tPE_parse_boot_argn(\"pcie_reset\", &pcie_reset, sizeof(pcie_reset));\n"
assert s.count(parse_anchor) == 1
s = s.replace(parse_anchor, parse_anchor + "\tPE_parse_boot_argn(\"pcie_power_cycle\", &pcie_power_cycle, sizeof(pcie_power_cycle));\n", 1)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-172 applied")
