import io
p = '/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c'
s = io.open(p, encoding='utf-8').read()
old = '\t\t\t\tprintf("pcie: 5:   21: nothing here touches memory; the page was filled before UFS\\n");\n\t\t\t\treturn;'
new = '''\t\t\t\t/* apply-163: the long sleeps were the killer, not memory.  Map the page
\t\t\t\t * and write to it: pcie_delay=0 and pcie_settle=100 keep every sleep short. */
\t\t\t\tif (pcie_dma_pa == 0) {
\t\t\t\t\tprintf("pcie: 5:   21: no dma page was taken before UFS\\n");
\t\t\t\t\treturn;
\t\t\t\t}
\t\t\t\tif (pcie_dma == 0) {
\t\t\t\t\tpcie_dma = ml_io_map_unmappable((vm_offset_t)pcie_dma_pa, PCIE_DMA_SIZE, VM_WIMG_IO);
\t\t\t\t}
\t\t\t\tprintf("pcie: 5:   21: mapped va 0x%llx\\n", (unsigned long long)pcie_dma);
\t\t\t\twr(pcie_dma, 0x41414141);
\t\t\t\tprintf("pcie: 5:   21: wrote 0x41414141, read back 0x%08x\\n", rd(pcie_dma));
\t\t\t\treturn;'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
io.open(p, 'w', encoding='utf-8', newline='').write(s)
print('apply-163 ok')