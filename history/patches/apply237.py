p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
src = open(p, encoding="utf-8", errors="replace").read()
old = """					for (i = 0; i < 100; i++) {
						uint32_t st = rd(bar0.base + 0x12c);

						if ((st >> 30) == 2 || (st >> 30) == 3) {
							break;
						}
						sleep_ms(100);
					}
"""
assert src.count(old) == 1, ("loop anchor", src.count(old))
new = """					/*
					 * apply-237: the guard proved the PBL reads through
					 * the owned context, so what is missing is the handoff
					 * itself.  Watch it at 1 ms resolution and print every
					 * change of status/EXECENV/MHISTATUS: a handoff that
					 * happens and is undone shows up here and nowhere else.
					 */
					{
						uint32_t last_st = 0xffffffffu, last_ee = 0xffffffffu;
						uint32_t last_mh = 0xffffffffu;

						for (i = 0; i < 3000; i++) {
							uint32_t st = rd(bar0.base + 0x12c);
							uint32_t ee = rd(bar0.base + 0x128);
							uint32_t mh = rd(bar0.base + 0x48);

							if (st != last_st || ee != last_ee || mh != last_mh) {
								printf("pcie: 5:   21: apply-237 t=%u st 0x%08x ee 0x%08x mh 0x%08x err 0x%08x\\n",
								    i, st, ee, mh, rd(bar0.base + 0x130));
								last_st = st;
								last_ee = ee;
								last_mh = mh;
							}
							if ((st >> 30) == 3) {
								break;
							}
							if (i > 50 && (st >> 30) == 2 && ee == 1) {
								break;
							}
							sleep_ms(1);
						}
						printf("pcie: 5:   21: apply-237 done after %u ms, errdbg %08x %08x %08x\\n",
						    i, rd(bar0.base + 0x134), rd(bar0.base + 0x138),
						    rd(bar0.base + 0x13c));
					}
"""
src = src.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(src)
print("apply-237 patched")