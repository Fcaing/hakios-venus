import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
a = "\t\t\t\t\tif (smmu_state == 1 && pcie_dma_extra != 0) {\n\t\t\t\t\t\tvolatile uint32_t *cc2"
assert s.count(a) == 1
s = s.replace(a, '''\t\t\t\t\tif (smmu_state == 1 && pcie_dma_extra != 0 && pcie_mhi_late0 != 0) {
\t\t\t\t\t\tuint32_t m0old = rd(bar0.base + 0x38);

\t\t\t\t\t\twr(bar0.base + 0x38, (m0old & ~0xff00u) | (2u << 8));
\t\t\t\t\t\tsleep_ms(5);
\t\t\t\t\t\tprintf("pcie: 5:   21: apply-286 m0 after mission: mh 0x%08x ee 0x%08x ctrl 0x%08x\\n",
\t\t\t\t\t\t    rd(bar0.base + 0x48), rd(bar0.base + 0x128), rd(bar0.base + 0x38));
\t\t\t\t\t}
\t\t\t\t\tif (smmu_state == 1 && pcie_dma_extra != 0) {
\t\t\t\t\t\tvolatile uint32_t *cc2''')
anchor = "static uint32_t pcie_chanstart2;"
assert s.count(anchor) == 1
s = s.replace(anchor, anchor + "\nstatic uint32_t pcie_mhi_late0;\t/* apply-286: ask for m0 once amss is up */")
a4 = 'PE_parse_boot_argn("pcie_mhi_m0late", &late, sizeof(late));'
assert s.count(a4) == 1
s = s.replace(a4, a4 + '''
								{
									uint32_t l0 = 0;
									if (PE_parse_boot_argn("pcie_mhi_late0", &l0, sizeof(l0))) {
										pcie_mhi_late0 = l0;
									}
								}''')
io.open(p, "w", encoding="utf-8").write(s)
print("apply-286: m0 after mission")