P = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
src = open(P).read()

# 1. declarations
a = "static uint32_t pcie_noearlystate;\t/* apply-361: write nothing to MHICTRL before ee 2 */"
assert src.count(a) == 1, ("decl", src.count(a))
src = src.replace(a, a + "\nstatic uint32_t pcie_ee2m0;\t/* apply-362: ask for m0 the instant ee 2 shows up */"
                     + "\nstatic uint32_t pcie_noearlydb;\t/* apply-362: no er doorbell before m0 is acked */")

# 2. parses
b = '\tPE_parse_boot_argn("pcie_noearlystate", &pcie_noearlystate, sizeof(pcie_noearlystate));'
assert src.count(b) == 1, ("parse", src.count(b))
src = src.replace(b, b + '\n\tPE_parse_boot_argn("pcie_ee2m0", &pcie_ee2m0, sizeof(pcie_ee2m0));'
                      + '\n\tPE_parse_boot_argn("pcie_noearlydb", &pcie_noearlydb, sizeof(pcie_noearlydb));')

# 3. the wait loop: m0 the moment ee becomes 2
c = """					{
						uint32_t k2;

						for (k2 = 0; k2 < 40; k2++) {"""
assert src.count(c) == 1, ("loop", src.count(c))
src = src.replace(c, """					{
						uint32_t k2, did362 = 0;

						for (k2 = 0; k2 < 40; k2++) {""")

d = """							if (e2 != cw || m2 != cm) {"""
assert src.count(d) == 1, ("loop2", src.count(d))
src = src.replace(d, """							if (pcie_ee2m0 != 0 && e2 == 2u && did362 == 0) {
								uint32_t o362 = rd(bar0.base + 0x38), w362;

								did362 = 1;
								wr(bar0.base + 0x38, (o362 & ~0xff00u) | (2u << 8));
								for (w362 = 0; w362 < 20u; w362++) {
									if ((rd(bar0.base + 0x48) & 0xffffff00u) == 0x200u) {
										break;
									}
									sleep_ms(1);
								}
								printf("pcie: 5:   21: apply-362 m0 the moment ee 2 showed: mh 0x%08x ctrl 0x%08x after %u ms\\n",
								    rd(bar0.base + 0x48), rd(bar0.base + 0x38), w362);
							}
							if (e2 != cw || m2 != cm) {""")

# 4. skip the pre-m0 er doorbells
e = """					if (smmu_state == 1 && pcie_dma_extra != 0 && pcie_mhi_late0 != 0 &&
					    rd(bar0.base + 0x128) == 2u) {"""
assert src.count(e) == 1, ("gate", src.count(e))
src = src.replace(e, """					if (smmu_state == 1 && pcie_dma_extra != 0 && pcie_mhi_late0 != 0 &&
					    pcie_noearlydb == 0 &&	/* apply-362 */
					    rd(bar0.base + 0x128) == 2u) {""")

open(P, "w").write(src)
print("apply-362 ok")
