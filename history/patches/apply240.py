import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
src = io.open(p, encoding="utf-8").read()
key = "apply-237 done after"
i = src.index(key)
tail = "rd(bar0.base + 0x13c));"
j = src.index(tail, i) + len(tail)
assert src[j] == "\n"
ins = '''
					/*
					 * apply-240: star's stage 11 programs the bus number
					 * register in the dbi; read it here first (read only) and
					 * also look at what the PBL left in the arena it was
					 * handed.
					 */
					{
						uint32_t *w = (uint32_t *)pcie_dma_extra;
						uint32_t words = PCIE_EXTRA_SIZE / 4;
						uint32_t k2, hits = 0;

						printf("pcie: 5:   21: apply-240 dbi 18 0x%08x dbi 4 0x%08x dbi 88 0x%08x bhi intvec 0x%08x\\n",
						    rd(dbi.base + 0x18), rd(dbi.base + 0x4),
						    rd(dbi.base + 0x88), rd(bar0.base + 0x120));
						for (k2 = 0; k2 < words; k2++) {
							if (w[k2] != 0) {
								if (hits < 8) {
									printf("pcie: 5:   21: apply-240 arena +0x%x = 0x%08x\\n",
									    k2 * 4, w[k2]);
								}
								hits++;
							}
						}
						printf("pcie: 5:   21: apply-240 arena non-zero words %u of %u\\n",
						    hits, words);
					}
					{
						uint32_t lw = 0;

						if (PE_parse_boot_argn("pcie_longwait", &lw, sizeof(lw)) && lw != 0) {
							uint32_t k2, last = rd(bar0.base + 0x128);

							for (k2 = 1; k2 <= lw; k2++) {
								uint32_t ee2 = rd(bar0.base + 0x128);
								uint32_t mh2 = rd(bar0.base + 0x48);

								if (ee2 != last || (mh2 & 1u) != 0) {
									printf("pcie: 5:   21: apply-240 long t=%u s ee 0x%08x mh 0x%08x st 0x%08x\\n",
									    k2, ee2, mh2, rd(bar0.base + 0x12c));
									last = ee2;
								}
								sleep_ms(1000);
							}
							printf("pcie: 5:   21: apply-240 long done ee 0x%08x mh 0x%08x st 0x%08x\\n",
							    rd(bar0.base + 0x128), rd(bar0.base + 0x48),
							    rd(bar0.base + 0x12c));
						}
					}'''
src = src[:j+1] + ins + src[j+1:]
io.open(p, "w", encoding="utf-8").write(src)
print("apply-240 applied at", j)