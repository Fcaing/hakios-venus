import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
key = "apply-232: bhi gets addr"
i = s.index(key)
tail = "(unsigned long long)bhi_addr, (unsigned long long)bhi_size,"
j = s.index(tail, i)
k = s.index(");", j) + 2
assert s[k] == "\n"
ins = '''
					/*
					 * apply-242: the two writes star makes before its bhi
					 * doorbell that this driver never made.  parf 0x174 bit 4
					 * is set by star and cleared here; dbi 0x18 is the bus
					 * number register star programs in stage 11 and this one
					 * leaves at zero.  Both are behind boot arguments so one
					 * run can tell which (if either) is the one that matters.
					 */
					{
						uint32_t v = 0;

						if (PE_parse_boot_argn("pcie_parf174", &v, sizeof(v)) && v != 0) {
							uint32_t old = rd(parf.base + 0x174);

							wr(parf.base + 0x174, old | (1u << 4));
							printf("pcie: 5:   21: apply-242 parf 174 0x%08x -> 0x%08x\\n",
							    old, rd(parf.base + 0x174));
						}
						v = 0;
						if (PE_parse_boot_argn("pcie_dbi18", &v, sizeof(v)) && v != 0) {
							uint32_t old = rd(dbi.base + 0x18);

							wr(dbi.base + 0x18, (old & 0xff000000u) | 0x010100u);
							printf("pcie: 5:   21: apply-242 dbi 18 0x%08x -> 0x%08x\\n",
							    old, rd(dbi.base + 0x18));
						}
						v = 0;
						if (PE_parse_boot_argn("pcie_bm", &v, sizeof(v)) && v != 0) {
							uint32_t old = rd(dbi.base + 0x4);

							wr(dbi.base + 0x4, old | 6u);
							printf("pcie: 5:   21: apply-242 dbi 4 0x%08x -> 0x%08x\\n",
							    old, rd(dbi.base + 0x4));
						}
					}'''
s = s[:k+1] + ins + s[k+1:]
io.open(p, "w", encoding="utf-8").write(s)
print("apply-242 applied at", k)