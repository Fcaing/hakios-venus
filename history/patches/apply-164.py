import io
p = '/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c'
s = io.open(p, encoding='utf-8').read()
old = '''\t\t\t\tprintf("pcie: 5:   21: wrote 0x41414141, read back 0x%08x\\n", rd(pcie_dma));
\t\t\t\treturn;'''
new = '''\t\t\t\tprintf("pcie: 5:   21: wrote 0x41414141, read back 0x%08x\\n", rd(pcie_dma));
\t\t\t\t/* apply-164: the bhi upload, as the star port does it (lemonade_wifi.c:719). */
\t\t\t\tif (!need(&bar0)) {
\t\t\t\t\treturn;
\t\t\t\t}
\t\t\t\tprintf("pcie: 5:   21: bhi before: soc 0x%08x ee 0x%08x mhi 0x%08x status 0x%08x err 0x%08x\\n",
\t\t\t\t       rd(bar0.base + 0x224), rd(bar0.base + 0x28), rd(bar0.base + 0x100),
\t\t\t\t       rd(bar0.base + 0x12c), rd(bar0.base + 0x130));
\t\t\t\twr(bar0.base + 0x12c, 0);
\t\t\t\twr(bar0.base + 0x10c, (uint32_t)(pcie_dma_pa >> 32));
\t\t\t\twr(bar0.base + 0x108, (uint32_t)pcie_dma_pa);
\t\t\t\twr(bar0.base + 0x110, PCIE_DMA_SIZE);
\t\t\t\twr(bar0.base + 0x118, 1);
\t\t\t\tsleep_ms(100);
\t\t\t\t{
\t\t\t\t\tuint32_t st = rd(bar0.base + 0x12c);
\t\t\t\t\tprintf("pcie: 5:   21: bhi after: status 0x%08x (top %u, ee %u) mhi 0x%08x err 0x%08x\\n",
\t\t\t\t\t       st, st >> 30, st & 0xff, rd(bar0.base + 0x100), rd(bar0.base + 0x130));
\t\t\t\t\tpcie_note("bhi 0x%08x mhi 0x%08x err 0x%08x; ", st,
\t\t\t\t\t          rd(bar0.base + 0x100), rd(bar0.base + 0x130));
\t\t\t\t}
\t\t\t\treturn;'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('apply-164 ok')