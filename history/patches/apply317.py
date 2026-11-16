import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

d = "static uint32_t pcie_full_win;"
assert s.count(d) == 1
s = s.replace(d, d + "\nstatic uint32_t pcie_wake2 = 1;\t/* apply-317: wake the device before the channel bell */")

a = """								d2 = 0;
								if (PE_parse_boot_argn("pcie_full_win", &d2, sizeof(d2))) {
									pcie_full_win = d2;
								}"""
assert s.count(a) == 1
s = s.replace(a, a + """
								d2 = 0;
								if (PE_parse_boot_argn("pcie_wake2", &d2, sizeof(d2))) {
									pcie_wake2 = d2;
								}""")

bell = """						wr(bar0.base + 0x300 + dch * 8 + 4u, 0u);
						wr(bar0.base + 0x300 + dch * 8, (uint32_t)trewp);"""
assert s.count(bell) == 1
s = s.replace(bell, """						/* apply-317: the vendor calls wake_toggle() right
						 * before it rings the channel doorbell, and the device
						 * idles in m2 between transfers.  Wake it first, ring,
						 * then ring once more in case the first bell landed
						 * while the engine was still waking up. */
						if (pcie_wake2 != 0) {
							wr(bar0.base + 0x6f8, 1u);
							wr(bar0.base + 0x6f8, 0u);
							printf("pcie: 5:   21: apply-317 woke the device before the bell: mh 0x%08x ee 0x%08x ctrl 0x%08x\\n",
							    rd(bar0.base + 0x48), rd(bar0.base + 0x128), rd(bar0.base + 0x38));
						}
						wr(bar0.base + 0x300 + dch * 8 + 4u, 0u);
						wr(bar0.base + 0x300 + dch * 8, (uint32_t)trewp);
						if (pcie_wake2 != 0) {
							sleep_ms(5);
							wr(bar0.base + 0x300 + dch * 8 + 4u, 0u);
							wr(bar0.base + 0x300 + dch * 8, (uint32_t)trewp);
							printf("pcie: 5:   21: apply-317 rang again: ch20 rp 0x%08x wp 0x%08x mh 0x%08x\\n",
							    rd(pcie_dma_extra + 20 * 0x2c + 0x1c), rd(pcie_dma_extra + 20 * 0x2c + 0x24),
							    rd(bar0.base + 0x48));
						}""")

io.open(p, "w", encoding="utf-8").write(s)
print("apply-317 written")