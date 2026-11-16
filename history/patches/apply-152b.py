p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(p).read()
old = '''\t\tif (kr == KERN_SUCCESS && buffer != 0) {
\t\t\tpcie_dma = buffer;
\t\t\tpcie_dma_pa = kvtophys(buffer);
\t\t\tprintf("pcie: dma init: pa 0x%llx, mapped at step 5\\n",
\t\t\t       (unsigned long long)pcie_dma_pa);
\t\t}'''
new = '''\t\tif (kr == KERN_SUCCESS && buffer != 0) {
\t\t\tpcie_dma = buffer;
\t\t\tpcie_dma_pa = kvtophys(buffer);
\t\t\tprintf("pcie: dma init: pa 0x%llx, mapped at step 5\\n",
\t\t\t       (unsigned long long)pcie_dma_pa);
\t\t\t/* apply-152: read the firmware here, at the head of the boot path,
\t\t\t * where memory still works, and stage the first block in the dma
\t\t\t * page.  By hakios_pcie_init() time nothing here can be touched. */
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
\t\t}'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
open(p, "w").write(s)
print("apply-152 firmware staging added")