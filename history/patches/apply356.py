import io
p="/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s=io.open(p,encoding="utf-8",errors="surrogateescape").read()
a='''						if (pcie_mission != 0) {
							uint32_t mt = rd(bar0.base + 0x38);

							wr(bar0.base + 0x38, (mt & ~0xff00u) | (4u << 8));
							sleep_ms(5);
							printf("pcie: 5:   21: apply-355 mission after the channels: mh 0x%08x ee 0x%08x ctrl 0x%08x\\n",
							    rd(bar0.base + 0x48), rd(bar0.base + 0x128), rd(bar0.base + 0x38));
						}'''
n='''						if (pcie_mission != 0) {
							uint32_t mt = rd(bar0.base + 0x38);

							/* apply-356: m1 (2) -> m3 (4) looks like an illegal jump: we wrote 4 and
							 * mhistatus stayed at 2.  Walk through m0 (1) the way a real link does. */
							wr(bar0.base + 0x38, (mt & ~0xff00u) | (1u << 8));
							sleep_ms(5);
							printf("pcie: 5:   21: apply-356 walked to state 1: mh 0x%08x ctrl 0x%08x\\n",
							    rd(bar0.base + 0x48), rd(bar0.base + 0x38));
							wr(bar0.base + 0x38, (mt & ~0xff00u) | (4u << 8));
							sleep_ms(5);
							printf("pcie: 5:   21: apply-356 walked to state 4: mh 0x%08x ctrl 0x%08x\\n",
							    rd(bar0.base + 0x48), rd(bar0.base + 0x38));
						}'''
assert s.count(a)==1, s.count(a)
s=s.replace(a,n)
io.open(p,"w",encoding="utf-8",errors="surrogateescape").write(s)
print("apply-356 ok")