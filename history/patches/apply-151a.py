p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(p).read()

# bar 21: print only, touch nothing
start = s.index("\t\t\tif (pcie_bar == 21) {")
end = s.index("\t\t\tif (pcie_bar == 20) {", start)
new2 = '''\t\t\tif (pcie_bar == 21) {
\t\t\t\t/*
\t\t\t\t * apply-151: printing only.  p134 proved that even *writing* a page that
\t\t\t\t * kmem_alloc_contig() handed us before UFS hangs the machine by this point,
\t\t\t\t * so nothing here touches memory at all; the page is filled at the head of
\t\t\t\t * the boot path and this step only reports what was taken.
\t\t\t\t */
\t\t\t\tprintf("pcie: 5:   21: dma page va 0x%llx pa 0x%llx size %u\\n",
\t\t\t\t       (unsigned long long)pcie_dma, (unsigned long long)pcie_dma_pa,
\t\t\t\t       (unsigned)pcie_dma_size);
\t\t\t\tprintf("pcie: 5:   21: nothing here touches memory; the page was filled before UFS\\n");
\t\t\t\treturn;
\t\t\t}
'''
s = s[:start] + new2 + s[end:]

# dma_init: 512 KiB instead of one page
old1 = "\t\tkr = kmem_alloc_contig(kernel_map, &buffer, PAGE_SIZE, PAGE_MASK, 0, 0,"
new1 = "\t\tkr = kmem_alloc_contig(kernel_map, &buffer, PCIE_DMA_SIZE, PAGE_MASK, 0, 0,"
assert s.count(old1) == 1, s.count(old1)
s = s.replace(old1, new1)
open(p, "w").write(s)
print("bar21 patched, size patched")