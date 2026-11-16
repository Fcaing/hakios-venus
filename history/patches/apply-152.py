p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(p).read()

# --- 1. dma_init: read amss.bin and copy the first block ---
old_tail = '''\t\tif (kr == KERN_SUCCESS && buffer != 0) {
\t\t\tpcie_dma = buffer;
\t\t\tpcie_dma_pa = kvtophys(buffer);
\t\t\tprintf("pcie: dma init: pa 0x%llx\\n", (unsigned long long)pcie_dma_pa);
\t\t}
\t}
}'''
new_tail = '''\t\tif (kr == KERN_SUCCESS && buffer != 0) {
\t\t\tpcie_dma = buffer;
\t\t\tpcie_dma_pa = kvtophys(buffer);
\t\t\tprintf("pcie: dma init: pa 0x%llx\\n", (unsigned long long)pcie_dma_pa);
\t\t\t/* apply-152: read the firmware here, at the head of the boot path, where
\t\t\t * memory still works, and stage the first block in the dma page.  By
\t\t\t * hakios_pcie_init() time nothing here can be touched again. */
\t\t\t{
\t\t\t\tuint64_t fsize = 0;
\t\t\t\tconst uint8_t *fw = hakios_image_file("fw", "amss.bin", &fsize, NULL);
\t\t\t\tprintf("pcie: dma init: amss.bin at 0x%llx, 0x%llx bytes\\n",
\t\t\t\t       (unsigned long long)fw, (unsigned long long)fsize);
\t\t\t\tif (fw != NULL && fsize >= 4) {
\t\t\t\t\tuint32_t n = fsize < PCIE_DMA_SIZE ? (uint32_t)fsize : PCIE_DMA_SIZE;
\t\t\t\t\tuint64_t i;
\t\t\t\t\tmemcpy((void *)pcie_dma, fw, n);
\t\t\t\t\tfor (i = 0; i < n; i += 64) {
\t\t\t\t\t\t__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma + i) : "memory");
\t\t\t\t\t}
\t\t\t\t\t__asm__ volatile ("dsb sy" : : : "memory");
\t\t\t\t\tprintf("pcie: dma init: copied %u bytes, first word 0x%08x\\n",
\t\t\t\t\t       n, rd(pcie_dma));
\t\t\t\t} else {
\t\t\t\t\tprintf("pcie: dma init: no usable amss.bin\\n");
\t\t\t\t}
\t\t\t}
\t\t}
\t}
}'''
assert s.count(old_tail) == 1
s = s.replace(old_tail, new_tail)

# --- 2. bar 21: write the BHI registers, poll the status ---
start = s.index("\t\t\tif (pcie_bar == 21) {")
end = s.index("\t\t\tif (pcie_bar == 20) {", start)
new21 = '''\t\t\tif (pcie_bar == 21) {
\t\t\t\t/* apply-152: the whole firmware upload, with nothing but MMIO:
\t\t\t\t * the page was filled before ufs and the bhi window is device memory. */
\t\t\t\tuint32_t status = 0;
\t\t\t\tint i;

\t\t\t\tif (pcie_dma_pa == 0) {
\t\t\t\t\tprintf("pcie: 5:   21: no dma page\\n");
\t\t\t\t\treturn;
\t\t\t\t}
\t\t\t\tprintf("pcie: 5:   21: dma pa 0x%llx, size %u\\n",
\t\t\t\t       (unsigned long long)pcie_dma_pa, (unsigned)pcie_dma_size);
\t\t\t\tprintf("pcie: 5:   21: bhi before: 0x%08x 0x%08x 0x%08x 0x%08x\\n",
\t\t\t\t       rd(bar0.base), rd(bar0.base + 0x28), rd(bar0.base + 0x128),
\t\t\t\t       rd(bar0.base + 0x12c));
\t\t\t\twr(bar0.base + 0x12c, 0);
\t\t\t\twr(bar0.base + 0x10c, (uint32_t)(pcie_dma_pa >> 32));
\t\t\t\twr(bar0.base + 0x108, (uint32_t)pcie_dma_pa);
\t\t\t\twr(bar0.base + 0x110, pcie_dma_size);
\t\t\t\twr(bar0.base + 0x118, 1);
\t\t\t\tprintf("pcie: 5:   21: bhi requested\\n");
\t\t\t\tfor (i = 0; i < 300; i++) {
\t\t\t\t\tstatus = rd(bar0.base + 0x12c);
\t\t\t\t\tif ((status >> 30) == 3) {
\t\t\t\t\t\tprintf("pcie: 5:   21: bhi error 0x%08x, ee %u\\n",
\t\t\t\t\t\t       status, status & 0xff);
\t\t\t\t\t\treturn;
\t\t\t\t\t}
\t\t\t\t\tif ((status >> 30) == 2) {
\t\t\t\t\t\tprintf("pcie: 5:   21: bhi done 0x%08x, ee %u\\n",
\t\t\t\t\t\t       status, status & 0xff);
\t\t\t\t\t\treturn;
\t\t\t\t\t}
\t\t\t\t\tsleep_ms(10);
\t\t\t\t}
\t\t\t\tprintf("pcie: 5:   21: bhi timed out, status 0x%08x\\n", status);
\t\t\t\tprintf("pcie: 5:   21: bhi after: 0x%08x 0x%08x 0x%08x 0x%08x\\n",
\t\t\t\t       rd(bar0.base), rd(bar0.base + 0x28), rd(bar0.base + 0x48),
\t\t\t\t       rd(bar0.base + 0x130));
\t\t\t\treturn;
\t\t\t}
'''
s = s[:start] + new21 + s[end:]
open(p, "w").write(s)
print("apply-152 written")