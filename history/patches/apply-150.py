p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(p).read()

# 1) dma_init must keep the VA too
old1 = '''\t\tif (kmem_alloc_contig(kernel_map, &buffer, PAGE_SIZE, PAGE_MASK, 0, 0,
\t\t    KMA_KOBJECT | KMA_ZERO | KMA_DATA, VM_KERN_MEMORY_IOKIT) == KERN_SUCCESS) {
\t\t\tpcie_dma_pa = kvtophys(buffer);'''
new1 = '''\t\tif (kmem_alloc_contig(kernel_map, &buffer, PAGE_SIZE, PAGE_MASK, 0, 0,
\t\t    KMA_KOBJECT | KMA_ZERO | KMA_DATA, VM_KERN_MEMORY_IOKIT) == KERN_SUCCESS) {
\t\t\tpcie_dma = buffer;
\t\t\tpcie_dma_pa = kvtophys(buffer);'''
print("anchor1 count", s.count(old1))

# 2) bar 21: no ml_io_map at all, use the kernel VA the allocation already handed us
start = s.index("\t\t\tif (pcie_bar == 21) {")
end = s.index("\t\t\tif (pcie_bar == 20) {", start)
new2 = '''\t\t\tif (pcie_bar == 21) {
\t\t\t\t/*
\t\t\t\t * apply-150: do not ml_io_map() the page at all.  Mapping a RAM page at
\t\t\t\t * this point of the boot hangs the machine (p133), the same way allocating
\t\t\t\t * one does (p127, p131), while mapping MMIO works (need(), p104).  The
\t\t\t\t * kernel VA that kmem_alloc_contig() returned at the head of the boot path
\t\t\t\t * is already usable, so the DMA buffer is touched through it and the
\t\t\t\t * physical address is what goes into the BHI registers.
\t\t\t\t */
\t\t\t\tif (pcie_dma_pa == 0 || pcie_dma == 0) {
\t\t\t\t\tprintf("pcie: 5:   21: no dma page was taken at the head of the boot path\\n");
\t\t\t\t\treturn;
\t\t\t\t}
\t\t\t\tprintf("pcie: 5:   21: dma page va 0x%llx pa 0x%llx\\n",
\t\t\t\t       (unsigned long long)pcie_dma, (unsigned long long)pcie_dma_pa);
\t\t\t\twr(pcie_dma, 0x41414141);
\t\t\t\tprintf("pcie: 5:   21: wrote 0x41414141 through the kernel va, read back 0x%08x\\n", rd(pcie_dma));
\t\t\t\treturn;
\t\t\t}
'''
s = s[:start] + new2 + s[end:]
s = s.replace(old1, new1)
open(p, "w").write(s)
print("patched")