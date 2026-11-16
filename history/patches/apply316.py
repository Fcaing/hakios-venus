import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old_decl = "static uint32_t pcie_mhi_state_val = 2;"
assert s.count(old_decl) == 1
s = s.replace(old_decl, old_decl + "\nstatic uint32_t pcie_full_win;\t/* apply-316: advertise the vendor's whole window */")

old_parse = """								d2 = 0;
								if (PE_parse_boot_argn("pcie_mhi_state_val", &d2, sizeof(d2))) {
									pcie_mhi_state_val = d2;
								}"""
assert s.count(old_parse) == 1
s = s.replace(old_parse, old_parse + """
								d2 = 0;
								if (PE_parse_boot_argn("pcie_full_win", &d2, sizeof(d2))) {
									pcie_full_win = d2;
								}""")

old_w = """					wr(bar0.base + 0x88, (uint32_t)(PCIE_EXTRA_IOVA + PCIE_EXTRA_SIZE));
					wr(bar0.base + 0x8c, 0u);"""
assert s.count(old_w) == 1
s = s.replace(old_w, """					/* apply-316: the retail device advertises 0xa0000000..0xb0000000.
					 * If the engine validates ring addresses against this window,
					 * a narrowed one would make it ignore perfectly good rings. */
					if (pcie_full_win != 0) {
						wr(bar0.base + 0x88, 0xb0000000u);
					} else {
						wr(bar0.base + 0x88, (uint32_t)(PCIE_EXTRA_IOVA + PCIE_EXTRA_SIZE));
					}
					wr(bar0.base + 0x8c, 0u);""")

old_w2 = """					wr(bar0.base + 0xa0, (uint32_t)(PCIE_EXTRA_IOVA + PCIE_EXTRA_SIZE));
					wr(bar0.base + 0xa4, 0u);"""
assert s.count(old_w2) == 1
s = s.replace(old_w2, """					if (pcie_full_win != 0) {
						wr(bar0.base + 0xa0, 0xb0000000u);
					} else {
						wr(bar0.base + 0xa0, (uint32_t)(PCIE_EXTRA_IOVA + PCIE_EXTRA_SIZE));
					}
					wr(bar0.base + 0xa4, 0u);""")

io.open(p, "w", encoding="utf-8").write(s)
print("apply-316 written")