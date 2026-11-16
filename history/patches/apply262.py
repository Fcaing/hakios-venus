import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

anchor = """\t\t\t\t\tprintf("pcie: 5:   21: apply-252 t=0 ee 0x%08x mh 0x%08x ctrl 0x%08x err 0x%08x\\n","""
assert s.count(anchor) == 1
block = '''\t\t\t\t\t/*
\t\t\t\t\t * apply-262: the firmware says a ring link request was
\t\t\t\t\t * issued and then timed out, and it dies 200 ms after the
\t\t\t\t\t * bhie handshake.  Watch the rings and the msi marker at
\t\t\t\t\t * 10 ms resolution from the first moment amss is up.  The
\t\t\t\t\t * msi data word is changed to 0x1234 first, so a second
\t\t\t\t\t * interrupt from amss cannot be mistaken for the one the
\t\t\t\t\t * bhi/bhie handshake already delivered.
\t\t\t\t\t */
\t\t\t\t\tif (PE_parse_boot_argn("pcie_msi_test", &want, sizeof(want)) && want != 0) {
\t\t\t\t\t\tue = (uint32_t)PCIE_SMMU_VEC_IOVA;
\t\t\t\t\t\twr(conf.base + 0x58, 0x00001234u);
\t\t\t\t\t\tprintf("pcie: 5:   21: apply-262 msi re-armed with data 0x00001234 at 0x%08x\\n", ue);
\t\t\t\t\t\tfor (w = 0; w < 400; w += 10) {
\t\t\t\t\t\t\tuint32_t er_wp, ch_wp, mark, ee3, k;
\t\t\t\t\t\t\tstatic uint32_t last_mark;

\t\t\t\t\t\t\tfor (k = 0; k < 0x8000; k += 64)
\t\t\t\t\t\t\t\t__asm__ volatile ("dc ivac, %0" :: "r" (pcie_dma_extra + k) : "memory");
\t\t\t\t\t\t\t__asm__ volatile ("dsb sy" ::: "memory");
\t\t\t\t\t\t\ter_wp = rd(pcie_dma_extra + 0x2028);
\t\t\t\t\t\t\tch_wp = rd(pcie_dma_extra + 20 * 0x30 + 0x28);
\t\t\t\t\t\t\tmark = rd(pcie_dma_vec);
\t\t\t\t\t\t\tee3 = rd(bar0.base + 0x128);
\t\t\t\t\t\t\tif (mark != last_mark || (w % 50) == 0) {
\t\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-262 t=%u mark 0x%08x er0 wp 0x%08x ch20 wp 0x%08x ee 0x%08x err 0x%08x\\n",
\t\t\t\t\t\t\t\t    w, mark, er_wp, ch_wp, ee3, rd(bar0.base + 0x130));
\t\t\t\t\t\t\t\tlast_mark = mark;
\t\t\t\t\t\t\t}
\t\t\t\t\t\t\tsleep_ms(10);
\t\t\t\t\t\t}
\t\t\t\t\t}
'''
s = s.replace(anchor, block + anchor)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-262 inserted", len(s))