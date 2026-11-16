import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
n0 = len(s)

anchor = "static uint32_t pcie_chanstart = 1;\t/* apply-265: send START_CHAN at once once amss is up */"
assert s.count(anchor) == 1, "a1"
s = s.replace(anchor, anchor + "\nstatic uint32_t pcie_mhi_erdb = 1;\t/* apply-266: ring the er doorbells before m0, as the vendor does */")

# parse it in the same place as the other mhi args
anchor = "\t\t\t\t\t\tPE_parse_boot_argn(\"pcie_chanstart\", &want, sizeof(want));\n\t\t\t\t\t\tpcie_chanstart = want;"
assert s.count(anchor) == 1, "a2"
s = s.replace(anchor, anchor + """
						{
							uint32_t want2 = pcie_mhi_erdb;

							PE_parse_boot_argn("pcie_mhi_erdb", &want2, sizeof(want2));
							pcie_mhi_erdb = want2;
						}""")

# ring the er doorbells right before m0
anchor = "\t\t\t\t\t\t\twr(bar0.base + 0x38, (rd(bar0.base + 0x38) & ~0xff00u) | (2u << 8));"
assert s.count(anchor) == 1, "a3"
s = s.replace(anchor, """							/*
							 * apply-266: the vendor ring_event_db()s every
							 * event ring before it asks for m0.  Do the same:
							 * the doorbell carries the wp iova of the ring.
							 */
							if (pcie_mhi_erdb != 0) {
								uint32_t e3;

								for (e3 = 0; e3 < 3; e3++) {
									uint64_t rb3 = PCIE_EXTRA_IOVA + 0x4000 + (uint64_t)e3 * 0x1000;

									wr(bar0.base + 0x700 + e3 * 8, (uint32_t)rb3);
								}
								printf("pcie: 5:   21: apply-266 er doorbells: er0 wp 0x%08x er1 0x%08x er2 0x%08x mh 0x%08x\\n",
								    rd(bar0.base + 0x700), rd(bar0.base + 0x708), rd(bar0.base + 0x710),
								    rd(bar0.base + 0x48));
							}
							wr(bar0.base + 0x38, (rd(bar0.base + 0x38) & ~0xff00u) | (2u << 8));""")

io.open(p, "w", encoding="utf-8").write(s)
print("patched", n0, "->", len(s))