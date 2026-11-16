import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

anchor = "static uint32_t pcie_mhi_m0late;\t/* apply-280: ask for m0 only after bhie */"
assert s.count(anchor) == 1
s = s.replace(anchor, anchor + "\nstatic uint32_t pcie_chanstart2;\t/* apply-282: start ipcr channels after mission mode */")

a2 = '\t\t\t\t\tif (pcie_mhi_watch != 0 && smmu_state == 1 && pcie_dma_extra != 0) {\n\t\t\t\t\t\tvolatile uint32_t *ex = (volatile uint32_t *)pcie_dma_extra;'
assert s.count(a2) == 1, s.count(a2)

block = '''\t\t\t\t\tif (pcie_chanstart2 != 0 && smmu_state == 1 && pcie_dma_extra != 0) {
\t\t\t\t\t\tvolatile uint32_t *cc2 = (volatile uint32_t *)(pcie_dma_extra + 0x2400);
\t\t\t\t\t\tvolatile uint32_t *cr2 = (volatile uint32_t *)(pcie_dma_extra + 0x7000);
\t\t\t\t\t\tuint64_t cbase2 = PCIE_EXTRA_IOVA + 0x7000;
\t\t\t\t\t\tuint64_t cwp2 = cbase2 + 0x40;
\t\t\t\t\t\tunsigned chs2[4];
\t\t\t\t\t\tunsigned i2, k2;

\t\t\t\t\t\tchs2[0] = 0; chs2[1] = 1; chs2[2] = 20; chs2[3] = 21;
\t\t\t\t\t\tfor (i2 = 0; i2 < 4; i2++) {
\t\t\t\t\t\t\tcr2[i2 * 4 + 0] = 0;
\t\t\t\t\t\t\tcr2[i2 * 4 + 1] = 0;
\t\t\t\t\t\t\tcr2[i2 * 4 + 2] = 0;
\t\t\t\t\t\t\tcr2[i2 * 4 + 3] = (chs2[i2] << 24) | (18u << 16);
\t\t\t\t\t\t}
\t\t\t\t\t\tcc2[0x0c / 4] = (uint32_t)cbase2;
\t\t\t\t\t\tcc2[0x10 / 4] = (uint32_t)(cbase2 >> 32);
\t\t\t\t\t\tcc2[0x14 / 4] = 0x1000;
\t\t\t\t\t\tcc2[0x1c / 4] = (uint32_t)cbase2;
\t\t\t\t\t\tcc2[0x20 / 4] = (uint32_t)(cbase2 >> 32);
\t\t\t\t\t\tcc2[0x24 / 4] = (uint32_t)cwp2;
\t\t\t\t\t\tcc2[0x28 / 4] = (uint32_t)(cwp2 >> 32);
\t\t\t\t\t\tfor (k2 = 0; k2 < 0x1000; k2 += 64) {
\t\t\t\t\t\t\t__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + 0x7000 + k2) : "memory");
\t\t\t\t\t\t}
\t\t\t\t\t\tfor (k2 = 0; k2 < 0x100; k2 += 64) {
\t\t\t\t\t\t\t__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + 0x2400 + k2) : "memory");
\t\t\t\t\t\t}
\t\t\t\t\t\t__asm__ volatile ("dsb sy" : : : "memory");
\t\t\t\t\t\tprintf("pcie: 5:   21: apply-282 chstart tre %08x %08x %08x %08x cc wp 0x%08x mh 0x%08x ee 0x%08x\\n",
\t\t\t\t\t\t    cr2[3], cr2[7], cr2[11], cr2[15], cc2[0x24 / 4],
\t\t\t\t\t\t    rd(bar0.base + 0x48), rd(bar0.base + 0x128));
\t\t\t\t\t\twr(bar0.base + 0x70, (uint32_t)cwp2);
\t\t\t\t\t\tfor (i2 = 0; i2 < 60; i2++) {
\t\t\t\t\t\t\tsleep_ms(5);
\t\t\t\t\t\t\tif (i2 % 10 == 0 || i2 == 59) {
\t\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-282 t=%u ms ee 0x%08x mh 0x%08x er0 rp 0x%08x wp 0x%08x\\n",
\t\t\t\t\t\t\t\t    (unsigned)(i2 * 5), rd(bar0.base + 0x128), rd(bar0.base + 0x48),
\t\t\t\t\t\t\t\t    rd(pcie_dma_extra + 0x201c), rd(pcie_dma_extra + 0x2024));
\t\t\t\t\t\t\t}
\t\t\t\t\t\t}
\t\t\t\t\t}
'''
s = s.replace(a2, block + a2)

a3 = 'PE_parse_boot_argn("pcie_mhi_m0late", &late, sizeof(late));'
assert s.count(a3) == 1
s = s.replace(a3, a3 + '''
\t\t\t\t\t\t\t\t{
\t\t\t\t\t\t\t\t\tuint32_t cs2 = 0;
\t\t\t\t\t\t\t\t\tif (PE_parse_boot_argn("pcie_chanstart2", &cs2, sizeof(cs2))) {
\t\t\t\t\t\t\t\t\t\tpcie_chanstart2 = cs2;
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t}''')
io.open(p, "w", encoding="utf-8").write(s)
print("apply-282 inserted")