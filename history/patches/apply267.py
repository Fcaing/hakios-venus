import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
n0 = len(s)

anchor = "static uint32_t pcie_mhi_erdb = 1;\t/* apply-266: ring the er doorbells before m0, as the vendor does */"
assert s.count(anchor) == 1, "a1"
s = s.replace(anchor, anchor + "\nstatic uint32_t pcie_mhi_nobase;\t/* apply-267: leave the mhi base/limit registers alone */")

# print the raw base/limit registers and honour nobase
old = """							wr(bar0.base + 0x84, (uint32_t)(lo >> 32));
							wr(bar0.base + 0x80, (uint32_t)lo);
							wr(bar0.base + 0x88, (uint32_t)hi);
							wr(bar0.base + 0x8c, (uint32_t)(hi >> 32));
							wr(bar0.base + 0x9c, (uint32_t)(lo >> 32));
							wr(bar0.base + 0x98, (uint32_t)lo);
							wr(bar0.base + 0xa0, (uint32_t)hi);
							wr(bar0.base + 0xa4, (uint32_t)(hi >> 32));"""
new = """							printf("pcie: 5:   21: apply-267 raw base 0x%08x:%08x limit 0x%08x:%08x data 0x%08x:%08x dlim 0x%08x:%08x nobase %u\\n",
							    rd(bar0.base + 0x84), rd(bar0.base + 0x80), rd(bar0.base + 0x8c), rd(bar0.base + 0x88),
							    rd(bar0.base + 0x9c), rd(bar0.base + 0x98), rd(bar0.base + 0xa4), rd(bar0.base + 0xa0),
							    pcie_mhi_nobase);
							if (pcie_mhi_nobase == 0) {
								wr(bar0.base + 0x84, (uint32_t)(lo >> 32));
								wr(bar0.base + 0x80, (uint32_t)lo);
								wr(bar0.base + 0x88, (uint32_t)hi);
								wr(bar0.base + 0x8c, (uint32_t)(hi >> 32));
								wr(bar0.base + 0x9c, (uint32_t)(lo >> 32));
								wr(bar0.base + 0x98, (uint32_t)lo);
								wr(bar0.base + 0xa0, (uint32_t)hi);
								wr(bar0.base + 0xa4, (uint32_t)(hi >> 32));
							}"""
assert s.count(old) == 1, "a2"
s = s.replace(old, new)

anchor = "\t\t\t\t\t\t\tPE_parse_boot_argn(\"pcie_mhi_erdb\", &want2, sizeof(want2));\n\t\t\t\t\t\t\tpcie_mhi_erdb = want2;"
assert s.count(anchor) == 1, "a3"
s = s.replace(anchor, anchor + """
							PE_parse_boot_argn("pcie_mhi_nobase", &want2, sizeof(want2));
							pcie_mhi_nobase = want2;""")

io.open(p, "w", encoding="utf-8").write(s)
print("patched", n0, "->", len(s))