import io
p="/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s=io.open(p,encoding="utf-8",errors="surrogateescape").read()

a1='static uint32_t pcie_mhi_data;	/* apply-292: push one data tre at the ipcr tx channel */'
n1=a1+'\nstatic uint32_t pcie_mission;	/* apply-355: walk to m2 before the data bell */'
assert s.count(a1)==1, ("a1",s.count(a1))
s=s.replace(a1,n1)

a2='''						printf("apply-335 enter, mh 0x%08x va 0x%llx\\n", rd(bar0.base + 0x48), (unsigned long long)pcie_dma_extra);'''
n2=a2+'''
						{
							uint32_t want9 = 0;

							if (PE_parse_boot_argn("pcie_mission", &want9, sizeof(want9))) {
								pcie_mission = want9;
							}
						}
						/* apply-355: the vendor leaves the device in m2, the mission state,
						 * while the data channels run and drops to m0 only for low power.
						 * We have always sat in m0: the command ring is serviced there but
						 * the data rings are not.  Walk up to m2 with the channels already
						 * running, then ring the data bell as usual. */
						if (pcie_mission != 0) {
							uint32_t mt = rd(bar0.base + 0x38);

							wr(bar0.base + 0x38, (mt & ~0xff00u) | (4u << 8));
							sleep_ms(5);
							printf("pcie: 5:   21: apply-355 mission after the channels: mh 0x%08x ee 0x%08x ctrl 0x%08x\\n",
							    rd(bar0.base + 0x48), rd(bar0.base + 0x128), rd(bar0.base + 0x38));
						}'''
assert s.count(a2)==1, ("a2",s.count(a2))
s=s.replace(a2,n2)
io.open(p,"w",encoding="utf-8",errors="surrogateescape").write(s)
print("apply-355 ok")