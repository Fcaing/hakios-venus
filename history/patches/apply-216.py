import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old = """					printf("pcie: 5:   21: bhi polls %u, status 0x%08x, mhi status 0x%08x (ready %u state %u)\\n",
					    i, rd(bar0.base + 0x12c), rd(bar0.base + 0x48),
					    rd(bar0.base + 0x48) & 1u, (rd(bar0.base + 0x48) >> 8) & 0xffu);
				}"""
assert s.count(old) == 1, s.count(old)
new = """					printf("pcie: 5:   21: bhi polls %u, status 0x%08x, mhi status 0x%08x (ready %u state %u)\\n",
					    i, rd(bar0.base + 0x12c), rd(bar0.base + 0x48),
					    rd(bar0.base + 0x48) & 1u, (rd(bar0.base + 0x48) >> 8) & 0xffu);
					/* apply-216: p211 got SUCCESS on the 4th poll but read
					 * MHISTATUS in the same breath and saw READY=0.  The vendor
					 * waits up to mhi,timeout (10 s, from the venus dtb) for SBL
					 * to come up, so wait the same way. */
					if ((rd(bar0.base + 0x12c) >> 30) == 2) {
						uint32_t k;

						for (k = 0; k < 150; k++) {
							if (rd(bar0.base + 0x48) & 1u) {
								break;
							}
							if (k == 20 || k == 60 || k == 120) {
								printf("pcie: 5:   21: mhi wait %u: status 0x%08x ee 0x%08x\\n",
								    k, rd(bar0.base + 0x48), rd(bar0.base + 0x128));
							}
							sleep_ms(100);
						}
						printf("pcie: 5:   21: mhi ready after %u polls: status 0x%08x (ready %u state %u) ee 0x%08x\\n",
						    k, rd(bar0.base + 0x48), rd(bar0.base + 0x48) & 1u,
						    (rd(bar0.base + 0x48) >> 8) & 0xffu, rd(bar0.base + 0x128));
						pcie_note("mhi ready %u status 0x%08x ee 0x%08x; ",
						    k, rd(bar0.base + 0x48), rd(bar0.base + 0x128));
					}
				}"""
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("ok apply-216")