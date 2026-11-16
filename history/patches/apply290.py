import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
anchor = '''\t\t\t\t\t\tprintf("pcie: 5:   21: apply-289 after er dbs: mh 0x%08x ee 0x%08x ctrl 0x%08x\\n",
\t\t\t\t\t\t    rd(bar0.base + 0x48), rd(bar0.base + 0x128), rd(bar0.base + 0x38));'''
assert s.count(anchor) == 1

dump = anchor + '''
\t\t\t\t\t\tsleep_ms(50);
\t\t\t\t\t\t{
\t\t\t\t\t\t\tunsigned d4;

\t\t\t\t\t\t\t__asm__ volatile ("dc ivac, %0" : : "r" (pcie_dma_extra + 0x4000) : "memory");
\t\t\t\t\t\t\t__asm__ volatile ("dsb sy" : : : "memory");
\t\t\t\t\t\t\tfor (d4 = 0; d4 < 4; d4++) {
\t\t\t\t\t\t\t\tvolatile uint32_t *e4 = (volatile uint32_t *)(pcie_dma_extra + 0x4000 + d4 * 16);

\t\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-290 er0[%02x] %08x %08x %08x %08x\\n",
\t\t\t\t\t\t\t\t    d4 * 16, e4[0], e4[1], e4[2], e4[3]);
\t\t\t\t\t\t\t}
\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-290 er0 rp 0x%08x wp 0x%08x ch20 0x%08x ch21 0x%08x\\n",
\t\t\t\t\t\t\t    *(volatile uint32_t *)(pcie_dma_extra + 0x201c),
\t\t\t\t\t\t\t    *(volatile uint32_t *)(pcie_dma_extra + 0x2024),
\t\t\t\t\t\t\t    *(volatile uint32_t *)(pcie_dma_extra + 20 * 0x2c),
\t\t\t\t\t\t\t    *(volatile uint32_t *)(pcie_dma_extra + 21 * 0x2c));
\t\t\t\t\t\t}'''
s = s.replace(anchor, dump)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-290 in, size", len(s))