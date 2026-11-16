p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(p).read()
start = s.index("\t\t\tif (pcie_bar == 21) {")
end = s.index("\t\t\tif (pcie_bar == 20) {", start)
old = s[start:end]
print("=== OLD (%d bytes) ===" % len(old))
new = '''\t\t\tif (pcie_bar == 21) {
\t\t\t\tuint32_t g4 = rd(gcc.base + 0x6b004), g0 = rd(gcc.base + 0x6b000);
\t\t\t\tuint32_t g24 = rd(gcc.base + 0x6b024), g1c = rd(gcc.base + 0x6b01c);
\t\t\t\tuint32_t g14 = rd(gcc.base + 0x6b014);
\t\t\t\t/* star's gate, printed only: 0x6b004 bit31 is the pcie gdsc, 0x6b000 bit0 the block
\t\t\t\t * reset, and bit31 of each AXI cbcr is "clock off" */
\t\t\t\tprintf("pcie: 5:   21: gcc 6b004=0x%08x 6b000=0x%08x 6b024=0x%08x 6b01c=0x%08x 6b014=0x%08x\\n",
\t\t\t\t       g4, g0, g24, g1c, g14);
\t\t\t\t/*
\t\t\t\t * apply-148: the page was taken at the head of the boot path
\t\t\t\t * (hakios_pcie_dma_init, before UFS), and it is mapped here the way need()
\t\t\t\t * maps the registers -- ml_io_map_unmappable(), which is the form that is
\t\t\t\t * known to work at this point.  Nothing is allocated here any more: any
\t\t\t\t * allocation at this point of the boot hangs the machine (p127, p131).
\t\t\t\t */
\t\t\t\tif (pcie_dma_pa == 0) {
\t\t\t\t\tprintf("pcie: 5:   21: no dma page was taken at the head of the boot path\\n");
\t\t\t\t\treturn;
\t\t\t\t}
\t\t\t\tif (pcie_dma == 0) {
\t\t\t\t\tpcie_dma = ml_io_map_unmappable((vm_offset_t)pcie_dma_pa, PAGE_SIZE, VM_WIMG_IO);
\t\t\t\t}
\t\t\t\tprintf("pcie: 5:   21: dma page pa 0x%llx -> va 0x%llx\\n",
\t\t\t\t       (unsigned long long)pcie_dma_pa, (unsigned long long)pcie_dma);
\t\t\t\tif (pcie_dma != 0) {
\t\t\t\t\twr(pcie_dma, 0x41414141);
\t\t\t\t\tprintf("pcie: 5:   21: wrote 0x41414141, read back 0x%08x\\n", rd(pcie_dma));
\t\t\t\t}
\t\t\t\treturn;
\t\t\t}
'''
s = s[:start] + new + s[end:]
open(p, "w").write(s)
print("=== patched (%d bytes) ===" % len(new))