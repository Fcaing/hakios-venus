import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
decl = "static uint32_t pcie_mhi_late0;"
assert s.count(decl) == 1
s = s.replace(decl, decl + "\nstatic uint32_t pcie_mhi_data;\t/* apply-292: push one data tre at the ipcr tx channel */")
old = 'if (PE_parse_boot_argn("pcie_mhi_nobase", &want2, sizeof(want2))) {'
assert s.count(old) == 1
s = s.replace(old, '{\n\t\t\t\t\t\t\t\tuint32_t d2 = 0;\n\n\t\t\t\t\t\t\t\tif (PE_parse_boot_argn("pcie_mhi_data", &d2, sizeof(d2))) {\n\t\t\t\t\t\t\t\t\tpcie_mhi_data = d2;\n\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t' + old)
key = 'apply-291 final rp 0x%08x'
i = s.index(key)
j = s.index("\n", s.index(");", i)) + 1
k = s.index("\t\t\t\t\t}\n", j) + len("\t\t\t\t\t}\n")
block = '''\t\t\t\t\tif (pcie_mhi_data != 0 && smmu_state == 1) {
\t\t\t\t\t\tuint64_t datiova = PCIE_EXTRA_IOVA + 0x3000;
\t\t\t\t\t\tuint64_t trewp = PCIE_EXTRA_IOVA + 0xc010;
\t\t\t\t\t\tuint32_t d9;

\t\t\t\t\t\tfor (d9 = 0; d9 < 16; d9++) {
\t\t\t\t\t\t\twr(pcie_dma_extra + 0x3000 + d9 * 4, 0xa5a5a5a5u);
\t\t\t\t\t\t}
\t\t\t\t\t\twr(pcie_dma_extra + 0xc000, (uint32_t)datiova);
\t\t\t\t\t\twr(pcie_dma_extra + 0xc004, (uint32_t)(datiova >> 32));
\t\t\t\t\t\twr(pcie_dma_extra + 0xc008, 0x40u);
\t\t\t\t\t\twr(pcie_dma_extra + 0xc00c, 0x00020200u);
\t\t\t\t\t\twr(pcie_dma_extra + 20 * 0x2c + 0x24, (uint32_t)trewp);
\t\t\t\t\t\twr(pcie_dma_extra + 20 * 0x2c + 0x28, (uint32_t)(trewp >> 32));
\t\t\t\t\t\tfor (d9 = 0x3000; d9 < 0xd000; d9 += 64) {
\t\t\t\t\t\t\t__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma_extra + d9) : "memory");
\t\t\t\t\t\t}
\t\t\t\t\t\t__asm__ volatile ("dsb sy" : : : "memory");
\t\t\t\t\t\tprintf("pcie: 5:   21: apply-292 send: tre ptr 0x%08x len 0x%08x dw1 0x%08x ch20 wp 0x%08x\\n",
\t\t\t\t\t\t    rd(pcie_dma_extra + 0xc000), rd(pcie_dma_extra + 0xc008),
\t\t\t\t\t\t    rd(pcie_dma_extra + 0xc00c), rd(pcie_dma_extra + 20 * 0x2c + 0x24));
\t\t\t\t\t\twr(bar0.base + 0x300 + 20 * 8, (uint32_t)trewp);
\t\t\t\t\t\tfor (d9 = 0; d9 < 40; d9++) {
\t\t\t\t\t\t\tsleep_ms(10);
\t\t\t\t\t\t\tif (d9 % 10 == 0) {
\t\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-292 t=%u ms ch20 rp 0x%08x wp 0x%08x er0 rp 0x%08x mh 0x%08x ee 0x%08x\\n",
\t\t\t\t\t\t\t\t    d9 * 10, rd(pcie_dma_extra + 20 * 0x2c + 0x1c), rd(pcie_dma_extra + 20 * 0x2c + 0x24),
\t\t\t\t\t\t\t\t    rd(pcie_dma_extra + 0x201c), rd(bar0.base + 0x48), rd(bar0.base + 0x128));
\t\t\t\t\t\t\t}
\t\t\t\t\t\t}
\t\t\t\t\t}
'''
s = s[:k] + block + s[k:]
io.open(p, "w", encoding="utf-8").write(s)
print("apply-292 in, size", len(s))