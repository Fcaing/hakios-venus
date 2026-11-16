import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
old = """							for (k2 = 1; k2 <= lw; k2++) {
								uint32_t ee2 = rd(bar0.base + 0x128);
								uint32_t mh2 = rd(bar0.base + 0x48);

								if (ee2 != last || (mh2 & 1u) != 0) {
									printf("pcie: 5:   21: apply-240 long t=%u s ee 0x%08x mh 0x%08x st 0x%08x\\n",
									    k2, ee2, mh2, rd(bar0.base + 0x12c));
									last = ee2;
								}
								sleep_ms(1000);
							}"""
new = """							for (k2 = 1; k2 <= lw; k2++) {
								uint32_t ee2 = rd(bar0.base + 0x128);
								uint32_t mh2 = rd(bar0.base + 0x48);

								/*
								 * apply-241: if the SBL started and then died
								 * the endpoint resets: the link would retrain
								 * and the bhi serial would change.  Watch all
								 * three once a second.
								 */
								printf("pcie: 5:   21: apply-241 t=%u s ee 0x%08x mh 0x%08x st 0x%08x link 0x%08x 0x%08x serial 0x%08x\\n",
								    k2, ee2, mh2, rd(bar0.base + 0x12c),
								    rd(dbi.base + 0x80), rd(dbi.base + 0x88),
								    rd(bar0.base + 0x140));
								last = ee2;
								sleep_ms(1000);
							}"""
assert s.count(old) == 1
io.open(p, "w", encoding="utf-8").write(s.replace(old, new))
print("apply-241 applied")