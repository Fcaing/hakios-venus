import io, re
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
key = "apply-240 arena non-zero words"
i = s.index(key)
j = s.index(");", s.index("%u of %u", i)) 
k = s.index(";", j) + 1
ins = '''
					/*
					 * apply-243: ring the doorbell a second time.  If the
					 * endpoint left the browser (that is, the pbl handed
					 * control to the sbl and the sbl crashed) the bhi will
					 * not answer any more.  If it answers again the pbl is
					 * still parked and nothing was ever executed.
					 */
					{
						uint32_t v = 0;

						if (PE_parse_boot_argn("pcie_rebell", &v, sizeof(v)) && v != 0) {
							uint32_t waited;
							uint32_t last_status = rd(bar0.base + 0x12c);
							uint32_t last_ee = rd(bar0.base + 0x128);
							uint32_t last_mh = rd(bar0.base + 0x38);

							printf("pcie: 5:   21: apply-243 before the second doorbell %u: st 0x%08x ee 0x%08x mh 0x%08x mhi 0x%08x\\n",
							    v, last_status, last_ee, last_mh, rd(bar0.base + 0x48));
							wr(bar0.base + 0x12c, 0);
							wr(bar0.base + 0x10c, (uint32_t)(bhi_addr >> 32));
							wr(bar0.base + 0x108, (uint32_t)bhi_addr);
							wr(bar0.base + 0x110, (uint32_t)bhi_size);
							wr(bar0.base + 0x118, v);
							for (waited = 0; waited < 3000; waited++) {
								uint32_t st = rd(bar0.base + 0x12c);
								uint32_t ee = rd(bar0.base + 0x128);

								if (st != last_status || ee != last_ee) {
									printf("pcie: 5:   21: apply-243 t=%u st 0x%08x ee 0x%08x mh 0x%08x\\n",
									    waited, st, ee, rd(bar0.base + 0x38));
									last_status = st;
									last_ee = ee;
								}
								if (st != 0) {
									break;
								}
								sleep_us(1000);
							}
							printf("pcie: 5:   21: apply-243 the second doorbell got st 0x%08x ee 0x%08x mh 0x%08x after %u ms\\n",
							    rd(bar0.base + 0x12c), rd(bar0.base + 0x128), rd(bar0.base + 0x38), waited);
						}
					}'''
s = s[:k+1] + ins + s[k+1:]
io.open(p, "w", encoding="utf-8").write(s)
print("apply-243 applied")