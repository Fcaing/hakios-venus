import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
orig_len = len(s)

anchor = "static uint32_t pcie_mhi_init = 1;\t/* apply-251: program the mhi mmio and ask for m0 */"
assert s.count(anchor) == 1, "anchor1"
s = s.replace(anchor, anchor + "\nstatic uint32_t pcie_chanstart = 1;\t/* apply-265: send START_CHAN at once once amss is up */")

old = "\t\t\t\t\tfor (st = 0, off = 0; off < 15000; off += 100) {"
new = "\t\t\t\t\tfor (st = 0, off = 0; off < 3000; off += 1) {"
assert s.count(old) == 1, "anchor2"
s = s.replace(old, new)
old = "\t\t\t\t\t\tsleep_ms(100);\n\t\t\t\t\t}"
assert s.count(old) == 1, "anchor3"
s = s.replace(old, "\t\t\t\t\t\tsleep_ms(1);\n\t\t\t\t\t}")

anchor = "\t\t\t\t\t\tPE_parse_boot_argn(\"pcie_mhi_init\", &want, sizeof(want));"
assert s.count(anchor) == 1, "anchor4"
s = s.replace(anchor, anchor + "\n\t\t\t\t\t\tPE_parse_boot_argn(\"pcie_chanstart\", &want, sizeof(want));\n\t\t\t\t\t\tpcie_chanstart = want;")

anchor = "\t\t\t\t\tpcie_note(\"bhie 0x%08x ee 0x%08x; \", st, rd(bar0.base + 0x128));"
assert s.count(anchor) == 1, "anchor5"
block = anchor + """
				/*
				 * apply-265: the firmware says it issued a ring link request
				 * and died 200 ms later.  The vendor host is already opening
				 * the channels at that moment (mhi_prepare_channel sends
				 * START_CHAN on the command ring and rings CRDB_LOWER), so do
				 * the same thing here while amss is still alive.
				 */
				if (pcie_chanstart != 0) {
					static const uint32_t cch[4] = { 0, 1, 20, 21 };
					uint32_t ci;
					uint32_t cw = rd(bar0.base + 0x128);
					uint32_t cm = rd(bar0.base + 0x48);
					uint64_t cbase = PCIE_EXTRA_IOVA + 0x7000;
					uint64_t cwp = cbase + 4 * 16;

					for (ci = 0; ci < 4; ci++) {
						wr(pcie_dma_extra + 0x7000 + ci * 16 + 0, 0);
						wr(pcie_dma_extra + 0x7000 + ci * 16 + 4, 0);
						wr(pcie_dma_extra + 0x7000 + ci * 16 + 8, 0);
						wr(pcie_dma_extra + 0x7000 + ci * 16 + 12, (cch[ci] << 24) | (18u << 16));
					}
					wr(pcie_dma_extra + 0x2400 + 0x28, (uint32_t)cwp);
					wr(pcie_dma_extra + 0x2400 + 0x2c, (uint32_t)(cwp >> 32));
					for (ci = 0; ci < 0x100; ci += 64) {
						__asm__ __volatile__("dc civac, %0" :: "r"(pcie_dma_extra + 0x7000 + ci) : "memory");
					}
					__asm__ __volatile__("dsb sy" ::: "memory");
					wr(bar0.base + 0x70, (uint32_t)cwp);
					printf("pcie: 5:   21: apply-265 start chan 0/1/20/21: cmd wp 0x%08x befor ee 0x%08x mh 0x%08x\\n",
					    (uint32_t)cwp, cw, cm);
					{
						uint32_t k2;

						for (k2 = 0; k2 < 40; k2++) {
							uint32_t e2 = rd(bar0.base + 0x128);
							uint32_t m2 = rd(bar0.base + 0x48);

							if (e2 != cw || m2 != cm) {
								printf("pcie: 5:   21: apply-265 t=%u ms ee 0x%08x mh 0x%08x\\n",
								    k2 * 5, e2, m2);
								cw = e2;
								cm = m2;
							}
							sleep_ms(5);
						}
					}
					printf("pcie: 5:   21: apply-265 done ee 0x%08x mh 0x%08x er0 rp 0x%08x wp 0x%08x cmdring %08x %08x %08x %08x\\n",
					    rd(bar0.base + 0x128), rd(bar0.base + 0x48),
					    rd(pcie_dma_extra + 0x2020), rd(pcie_dma_extra + 0x2028),
					    rd(pcie_dma_extra + 0x7000), rd(pcie_dma_extra + 0x7004),
					    rd(pcie_dma_extra + 0x7008), rd(pcie_dma_extra + 0x700c));
				}
"""
s = s.replace(anchor, block)
io.open(p, "w", encoding="utf-8").write(s)
print("patched", orig_len, "->", len(s))