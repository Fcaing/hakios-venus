import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

# 1. declaration
old1 = "static uint32_t pcie_retrain = 1;"
assert s.count(old1) == 1
s = s.replace(old1, old1 + "\nstatic uint32_t pcie_ee1settle; /* apply-349: how long to leave sbl alone after it reports ee 1 */")

# 2. settle right after the bhi-done print
old2 = """						printf("pcie: 5:   21: apply-237 done after %u ms, errdbg %08x %08x %08x\\n",
						    i, rd(bar0.base + 0x134), rd(bar0.base + 0x138),
						    rd(bar0.base + 0x13c));
"""
assert s.count(old2) == 1
new2 = old2 + """						/* apply-349: the endpoint crashes about 20 ms after it
						 * announces ee 1.  Give sbl room before touching
						 * anything at all.
						 */
						{
							uint32_t es = pcie_ee1settle;

							if (PE_parse_boot_argn("pcie_ee1settle", &es,
							    sizeof(es))) {
								pcie_ee1settle = es;
							}
						}
						if (pcie_ee1settle != 0) {
							sleep_ms(pcie_ee1settle);
							printf("pcie: 5:   21: apply-349 settled %u ms after ee 1: mh %08x ee %08x\\n",
							    pcie_ee1settle, rd(bar0.base + 0x48),
							    rd(bar0.base + 0x128));
						}
"""
s = s.replace(old2, new2)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-349 ok")