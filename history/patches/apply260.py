import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
anchor = '\t\t\t\t\tprintf("pcie: 5:   21: apply-252 done ee 0x%08x mh 0x%08x ctrl 0x%08x err 0x%08x\\n",'
assert s.count(anchor) == 1
block = '''\t\t\t\t\t/*
\t\t\t\t\t * apply-260: the firmware says a ring link request
\t\t\t\t\t * timed out.  Before believing the rings are empty,
\t\t\t\t\t * remember our cpu may still hold stale lines for
\t\t\t\t\t * memory the device has written.  Drop them and
\t\t\t\t\t * look again, a few times.
\t\t\t\t\t */
\t\t\t\t\t{
\t\t\t\t\t\tuint32_t k, pass;
\t\t\t\t\t\tuint32_t prev_er = 0xffffffffu, prev_ch = 0xffffffffu;

\t\t\t\t\t\tfor (pass = 0; pass < 30; pass++) {
\t\t\t\t\t\t\tuint32_t er_wp, ch_wp, first, ee2;

\t\t\t\t\t\t\tfor (k = 0; k < 0x8000; k += 64)
\t\t\t\t\t\t\t\t__asm__ volatile ("dc ivac, %0" :: "r" (pcie_dma_extra + k) : "memory");
\t\t\t\t\t\t\t__asm__ volatile ("dsb sy" ::: "memory");
\t\t\t\t\t\t\ter_wp = rd(pcie_dma_extra + 0x2028);
\t\t\t\t\t\t\tch_wp = rd(pcie_dma_extra + 20 * 0x30 + 0x28);
\t\t\t\t\t\t\tfirst = rd(pcie_dma_extra + 0x4000);
\t\t\t\t\t\t\tee2 = rd(bar0.base + 0x128);
\t\t\t\t\t\t\tif (pass == 0 || er_wp != prev_er || ch_wp != prev_ch)
\t\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-260 t=%u er0 wp 0x%08x ch20 wp 0x%08x er0[0] 0x%08x ee 0x%08x ch20[0] 0x%08x\\n",
\t\t\t\t\t\t\t\t    pass * 20, er_wp, ch_wp, first, ee2,
\t\t\t\t\t\t\t\t    rd(pcie_dma_extra + 20 * 0x30 + 0x20));
\t\t\t\t\t\t\tprev_er = er_wp;
\t\t\t\t\t\t\tprev_ch = ch_wp;
\t\t\t\t\t\t\tsleep_ms(20);
\t\t\t\t\t\t}
\t\t\t\t\t}
'''
s = s.replace(anchor, block + anchor)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-260 inserted", len(s))