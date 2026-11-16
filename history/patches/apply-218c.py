import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
def sub1(old, new):
    global s
    assert s.count(old) == 1, ("count", s.count(old), old[:80])
    s = s.replace(old, new, 1)

# remember the firmware size so the vector table can cover the whole image
sub1("""static uint32_t pcie_dma_staged;
""", """static uint32_t pcie_dma_staged;
static uint64_t pcie_fw_size;   /* apply-218: the size of amss.bin */
""")
sub1("""	pcie_dma_staged = 1;
	printf("pcie: stage: copied %u bytes of 0x%llx from amss.bin to 0x%llx (pa 0x%llx), first word 0x%08x\\n",
""", """	pcie_dma_staged = 1;
	pcie_fw_size = fsize;
	printf("pcie: stage: copied %u bytes of 0x%llx from amss.bin to 0x%llx (pa 0x%llx), first word 0x%08x\\n",
""")

start = s.find("\t\t\t\t#if 0 /* apply-210: BHI only;")
assert start > 0, "no start"
end_marker = "\t\t\t\t\t\tpcie_note(\"bhie 0x%08x; \", st);\n\t\t\t\t\t}\n\t\t\t\t}\n\t\t\t\t#endif\n"
end = s.find(end_marker, start)
assert end > 0, "no end"
end += len(end_marker)

new = """\t\t\t\t/*
\t\t\t\t * apply-218: the BHIE path.  venus's PBL answers the BHI doorbell
\t\t\t\t * with SUCCESS (p210-p213) but never moves EXECENV off PBL, so
\t\t\t\t * nothing ever runs the 512 KiB it received.  star's
\t\t\t\t * mhi_full_firmware (lemonade_wifi.c:1159) instead hands the
\t\t\t\t * endpoint a vector table covering the whole image, 512 KiB per
\t\t\t\t * entry, and rings TXVECDB.  The image lives in the 8 MiB region
\t\t\t\t * the SMMU now maps.
\t\t\t\t */
\t\t\t\tif (smmu_state == 1 && pcie_dma_extra != 0 && pcie_dma_vec_pa != 0 &&
\t\t\t\t    pcie_fw_size != 0) {
\t\t\t\t\tuint32_t st = 0, seq = 0;
\t\t\t\t\tuint64_t off;
\t\t\t\t\tuint32_t count = 0;
\t\t\t\t\tvm_offset_t vec;

\t\t\t\t\t/* p134: the kernel VA from kmem_alloc_contig is not writable
\t\t\t\t\t * here; p163 showed the unmappable alias is. */
\t\t\t\t\tvec = ml_io_map_unmappable((vm_offset_t)pcie_dma_vec_pa,
\t\t\t\t\t    PAGE_SIZE, VM_WIMG_IO);
\t\t\t\t\tif (vec == 0) {
\t\t\t\t\t\tprintf("pcie: 5:   21: bhie: cannot map the vector page\\n");
\t\t\t\t\t}
\t\t\t\t\tfor (off = 0; off < pcie_fw_size && count < 64; off += PCIE_DMA_SIZE) {
\t\t\t\t\t\tuint64_t left = pcie_fw_size - off;
\t\t\t\t\t\tuint64_t iova = PCIE_EXTRA_IOVA + PCIE_EXTRA_DATA_OFF + off;

\t\t\t\t\t\twr(vec + count * 16 + 0, (uint32_t)iova);
\t\t\t\t\t\twr(vec + count * 16 + 4, (uint32_t)(iova >> 32));
\t\t\t\t\t\twr(vec + count * 16 + 8, (uint32_t)(left < PCIE_DMA_SIZE ? left : PCIE_DMA_SIZE));
\t\t\t\t\t\twr(vec + count * 16 + 12, 0);
\t\t\t\t\t\tcount++;
\t\t\t\t\t}
\t\t\t\t\t__asm__ volatile ("dc civac, %0" : : "r" (vec) : "memory");
\t\t\t\t\t__asm__ volatile ("dsb sy" : : : "memory");
\t\t\t\t\tprintf("pcie: 5:   21: bhie %u vectors, image 0x%llx bytes at iova 0x%llx, first 0x%08x 0x%08x 0x%08x\\n",
\t\t\t\t\t    count, (unsigned long long)pcie_fw_size,
\t\t\t\t\t    (unsigned long long)(PCIE_EXTRA_IOVA + PCIE_EXTRA_DATA_OFF),
\t\t\t\t\t    rd(vec + 0), rd(vec + 4), rd(vec + 8));
\t\t\t\t\twr(bar0.base + 0x224 + 0x44, 0);
\t\t\t\t\twr(bar0.base + 0x224 + 0x30, (uint32_t)(PCIE_SMMU_VEC_IOVA >> 32));
\t\t\t\t\twr(bar0.base + 0x224 + 0x2c, (uint32_t)PCIE_SMMU_VEC_IOVA);
\t\t\t\t\twr(bar0.base + 0x224 + 0x34, count * 16);
\t\t\t\t\t{
\t\t\t\t\t\tstatic uint32_t seed = 0x0badf00du;

\t\t\t\t\t\tseed = seed * 1103515245u + 12345u;
\t\t\t\t\t\tseq = (seed >> 2) & 0x3fffffffu;
\t\t\t\t\t\tif (seq == 0) {
\t\t\t\t\t\t\tseq = 1;
\t\t\t\t\t\t}
\t\t\t\t\t}
\t\t\t\t\tprintf("pcie: 5:   21: bhie db 0x%08x, addr 0x%08x:%08x size %u ee 0x%08x\\n",
\t\t\t\t\t    seq, rd(bar0.base + 0x224 + 0x30), rd(bar0.base + 0x224 + 0x2c),
\t\t\t\t\t    rd(bar0.base + 0x224 + 0x34), rd(bar0.base + 0x128));
\t\t\t\t\twr(bar0.base + 0x224 + 0x3c, seq);
\t\t\t\t\tfor (st = 0, off = 0; off < 15000; off += 100) {
\t\t\t\t\t\tst = rd(bar0.base + 0x224 + 0x44);
\t\t\t\t\t\tif ((st >> 30) == 2 || (st >> 30) == 3) {
\t\t\t\t\t\t\tbreak;
\t\t\t\t\t\t}
\t\t\t\t\t\tif (off == 2000 || off == 6000 || off == 12000) {
\t\t\t\t\t\t\tprintf("pcie: 5:   21: bhie wait %u: status 0x%08x ee 0x%08x fsr 0x%08x\\n",
\t\t\t\t\t\t\t    (unsigned)off, st, rd(bar0.base + 0x128), rd(smmu_cb + 0x58));
\t\t\t\t\t\t}
\t\t\t\t\t\tsleep_ms(100);
\t\t\t\t\t}
\t\t\t\t\tprintf("pcie: 5:   21: bhie after %u ms: status 0x%08x (top %u, seq 0x%08x) ee 0x%08x fsr 0x%08x far 0x%08x:%08x\\n",
\t\t\t\t\t    (unsigned)off, st, st >> 30, st & 0x3fffffffu, rd(bar0.base + 0x128),
\t\t\t\t\t    rd(smmu_cb + 0x58), rd(smmu_cb + 0x64), rd(smmu_cb + 0x60));
\t\t\t\t\tpcie_note("bhie 0x%08x ee 0x%08x; ", st, rd(bar0.base + 0x128));
\t\t\t\t}
"""
s = s[:start] + new + s[end:]
io.open(p, "w", encoding="utf-8").write(s)
print("ok apply-218 part 3")