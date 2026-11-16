P = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
src = open(P).read()

a = "static uint32_t pcie_noearlydb;\t/* apply-362: no er doorbell before m0 is acked */"
assert src.count(a) == 1
src = src.replace(a, a + "\nstatic uint32_t pcie_resetpulse;\t/* apply-363: pulse MHICTRL.RESET like mhi_reset() does */")

b = '\tPE_parse_boot_argn("pcie_noearlydb", &pcie_noearlydb, sizeof(pcie_noearlydb));'
assert src.count(b) == 1
src = src.replace(b, b + '\n\tPE_parse_boot_argn("pcie_resetpulse", &pcie_resetpulse, sizeof(pcie_resetpulse));')

c = """								printf("pcie: 5:   21: apply-362 m0 the moment ee 2 showed: mh 0x%08x ctrl 0x%08x after %u ms\\n",
								    rd(bar0.base + 0x48), rd(bar0.base + 0x38), w362);"""
assert src.count(c) == 1
src = src.replace(c, c + """
								if (pcie_resetpulse != 0) {
									uint32_t o363 = rd(bar0.base + 0x38), w363;

									wr(bar0.base + 0x38, (o363 & ~0xff00u) | 1u);
									sleep_ms(10);
									wr(bar0.base + 0x38, (o363 & ~0xff00u));
									for (w363 = 0; w363 < 20u; w363++) {
										if ((rd(bar0.base + 0x48) & 1u) == 0u) {
											break;
										}
										sleep_ms(1);
									}
									printf("pcie: 5:   21: apply-363 reset pulse: mh 0x%08x ctrl 0x%08x after %u ms\\n",
									    rd(bar0.base + 0x48), rd(bar0.base + 0x38), w363);
									wr(bar0.base + 0x38, (rd(bar0.base + 0x38) & ~0xff00u) | (2u << 8));
									for (w363 = 0; w363 < 50u; w363++) {
										if ((rd(bar0.base + 0x48) & 0xffffff00u) == 0x200u) {
											break;
										}
										sleep_ms(1);
									}
									printf("pcie: 5:   21: apply-363 back to m0: mh 0x%08x ctrl 0x%08x after %u ms\\n",
									    rd(bar0.base + 0x48), rd(bar0.base + 0x38), w363);
								}""")

open(P, "w").write(src)
print("apply-363 ok")
