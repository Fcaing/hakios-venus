import io

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
lines = io.open(p, encoding="utf-8").read().split("\n")
# 1576-1666 are 1-based; replace them
start = 1576 - 1
end = 1666  # exclusive index
assert "hakios_pcie_dma_init" in lines[start], lines[start]
assert lines[end - 1] == "}", lines[end - 1]
new = """hakios_pcie_dma_init(void)
{
\tuint32_t wants = 0;
\tkern_return_t kr;

\tif (pcie_dma != 0 || !PE_parse_boot_argn("pcie", &wants, sizeof(wants)) || wants == 0) {
\t\treturn;
\t}
\t{
\t\tuint32_t skip = 0;
\t\tif (PE_parse_boot_argn("pcie_dma_skip", &skip, sizeof(skip)) && skip != 0) {
\t\t\tprintf("pcie: dma init: skipped on request\\n");
\t\t\treturn;
\t\t}
\t}
\tif (PE_parse_boot_argn("pcie_dma_pa", &pcie_dma_pa, sizeof(pcie_dma_pa)) && pcie_dma_pa != 0) {
\t\tprintf("pcie: dma init: the loader's page 0x%llx\\n", (unsigned long long)pcie_dma_pa);
\t\treturn;
\t}
\t{
\t\tvm_offset_t buffer = 0;
\t\tkr = kmem_alloc_contig(kernel_map, &buffer, PCIE_DMA_SIZE, PAGE_MASK, 0, 0,
\t\t    KMA_KOBJECT | KMA_ZERO | KMA_DATA, VM_KERN_MEMORY_IOKIT);
\t\tif (kr == KERN_SUCCESS && buffer != 0) {
\t\t\tpcie_dma = buffer;
\t\t\tpcie_dma_pa = kvtophys(buffer);
\t\t\tprintf("pcie: dma init: page at 0x%llx, pa 0x%llx, 0x%x bytes\\n",
\t\t\t       (unsigned long long)pcie_dma, (unsigned long long)pcie_dma_pa,
\t\t\t       (unsigned int)PCIE_DMA_SIZE);
\t\t} else {
\t\t\tprintf("pcie: dma init: kmem_alloc_contig -> kr %d, va 0x%llx\\n",
\t\t\t       kr, (unsigned long long)buffer);
\t\t}
\t}
}

/*
 * apply-173: the firmware is read here, after UFS is up and before
 * hakios_pcie_init() runs.  Reading it in hakios_pcie_dma_init() panicked
 * (p140/p142/p143) because hakios_image_file() walks md0, which lives on the
 * UFS volume, and the UFS driver has not been started at that point.
 */
void
hakios_pcie_stage(void)
{
\tuint64_t fsize = 0;
\tconst uint8_t *fw;
\tuint32_t n;
\tuint64_t i;

\tif (pcie_dma == 0 || pcie_dma_pa == 0 || pcie_dma_staged != 0) {
\t\treturn;
\t}
\tfw = hakios_image_file("fw", "amss.bin", &fsize, NULL);
\tif (fw == NULL || fsize < 4) {
\t\tprintf("pcie: stage: no usable amss.bin (0x%llx bytes)\\n", (unsigned long long)fsize);
\t\treturn;
\t}
\tn = fsize < PCIE_DMA_SIZE ? (uint32_t)fsize : PCIE_DMA_SIZE;
\tmemcpy((void *)pcie_dma, fw, n);
\tfor (i = 0; i < n; i += 64) {
\t\t__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma + i) : "memory");
\t}
\t__asm__ volatile ("dsb sy" : : : "memory");
\tpcie_dma_staged = 1;
\tprintf("pcie: stage: copied %u bytes of 0x%llx from amss.bin to 0x%llx (pa 0x%llx), first word 0x%08x\\n",
\t       n, (unsigned long long)fsize, (unsigned long long)pcie_dma,
\t       (unsigned long long)pcie_dma_pa, rd(pcie_dma));
}"""
lines[start:end] = new.split("\n")
s = "\n".join(lines)

anchor = "static uint32_t pcie_bar;\n"
assert s.count(anchor) == 1
s = s.replace(anchor, anchor + "static uint32_t pcie_dma_staged;\n", 1)
io.open(p, "w", encoding="utf-8").write(s)

q = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.input.c"
t = io.open(q, encoding="utf-8").read()
old = "\t/* apply-155: dma_init left out, p142/p143 panic with pcie=1 and nothing else */\n\t/* hakios_pcie_dma_init(); */\n"
assert t.count(old) == 1
t = t.replace(old, "\t/* apply-173: the page here, the firmware after UFS */\n\thakios_pcie_dma_init();\n", 1)
old2 = "\thakios_wifi_init();\n\thakios_pcie_init();\n"
assert t.count(old2) == 1
t = t.replace(old2, "\thakios_wifi_init();\n\thakios_pcie_stage();\n\thakios_pcie_init();\n", 1)
old3 = "extern void hakios_pcie_dma_init(void);\n"
assert t.count(old3) == 1
t = t.replace(old3, old3 + "extern void hakios_pcie_stage(void);\n", 1)
io.open(q, "w", encoding="utf-8").write(t)
print("apply-173 applied")
