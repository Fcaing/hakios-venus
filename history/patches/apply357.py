import io
p="/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s=io.open(p,encoding="utf-8",errors="surrogateescape").read()

a1='static uint32_t pcie_mission;	/* apply-355: walk to m2 before the data bell */'
n1=a1+'\nstatic uint32_t pcie_erfull;	/* apply-357: dump the whole event ring raw */'
assert s.count(a1)==1, ("a1",s.count(a1))
s=s.replace(a1,n1)

a2='\t\t\t\t\t\tprintf("pcie: 5:   21: apply-282 chstart tre %08x %08x %08x %08x cc wp 0x%08x mh 0x%08x ee 0x%08x\\n",'
ins='''						/* apply-357: dump the whole er0 ring.  The device fills all 32 slots
						 * (wp runs to ...4ff0), so every event it ever sent is still there:
						 * state changes, ee events, bw requests and the command
						 * completions.  We never decoded the state/ee fields, so print the
						 * raw words plus the decoded type byte for each entry. */
						{
							uint32_t want10 = 0, ie;

							if (PE_parse_boot_argn("pcie_erfull", &want10, sizeof(want10))) {
								pcie_erfull = want10;
							}
							if (pcie_erfull != 0) {
								printf("pcie: 5:   21: apply-357 er0 ctx rp 0x%08x wp 0x%08x mh 0x%08x ee 0x%08x\\n",
								    rd(pcie_dma_extra + 0x201c), rd(pcie_dma_extra + 0x2024),
								    rd(bar0.base + 0x48), rd(bar0.base + 0x128));
								for (ie = 0; ie < 32u; ie++) {
									volatile uint32_t *e9 = (volatile uint32_t *)(pcie_dma_extra + 0x4000 + ie * 16u);

									__asm__ volatile ("dc ivac, %0" : : "r" (e9) : "memory");
									printf("pcie: 5:   21: apply-357 er[%02x] %08x %08x %08x %08x type %02x hi %02x aux %04x\\n",
									    ie, e9[0], e9[1], e9[2], e9[3],
									    (e9[3] >> 16) & 0xffu, (e9[3] >> 24) & 0xffu, e9[3] & 0xffffu);
								}
							}
						}
'''
assert s.count(a2)==1, ("a2",s.count(a2))
s=s.replace(a2, ins+a2)
io.open(p,"w",encoding="utf-8",errors="surrogateescape").write(s)
print("apply-357 ok")