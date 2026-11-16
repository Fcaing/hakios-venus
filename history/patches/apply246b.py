import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
before = len(s)

arm = """\t\t\t\t/*
\t\t\t\t * apply-246: the vendor's own log shows the endpoint raising
\t\t\t\t * its completion interrupt 317 ms after the BHI doorbell,
\t\t\t\t * and mhi_intvec_handlr running in that same millisecond.
\t\t\t\t * We have never seen an interrupt because the msi address is
\t\t\t\t * whatever the bootloader left there.  Point it at the
\t\t\t\t * vector page -- mapped, and unused when pcie_novec=1 --
\t\t\t\t * fill that page with a marker, and read it back below.
\t\t\t\t */
\t\t\t\tif (pcie_msi_test != 0 && smmu_state == 1 && pcie_dma_vec_pa != 0) {
\t\t\t\t\tvm_offset_t mv = ml_io_map_unmappable(
\t\t\t\t\t    (vm_offset_t)pcie_dma_vec_pa, PAGE_SIZE, VM_WIMG_IO);
\t\t\t\t\tuint32_t cap = rd(conf.base + 0x50);
\t\t\t\t\tuint32_t doff = (cap & 0x80u) ? 0x5cu : 0x58u;
\t\t\t\t\tuint32_t moff = (cap & 0x80u) ? 0x60u : 0x5cu;
\t\t\t\t\tuint32_t k;

\t\t\t\t\tif (mv != 0) {
\t\t\t\t\t\tfor (k = 0; k < 4096; k += 4) {
\t\t\t\t\t\t\twr(mv + k, 0xa5a5a5a5u);
\t\t\t\t\t\t}
\t\t\t\t\t\tfor (k = 0; k < 4096; k += 64) {
\t\t\t\t\t\t\t__asm__ __volatile__("dc civac, %0"
\t\t\t\t\t\t\t    :: "r"(mv + (vm_offset_t)k) : "memory");
\t\t\t\t\t\t}
\t\t\t\t\t\t__asm__ __volatile__("dsb sy" ::: "memory");
\t\t\t\t\t\twr(conf.base + moff, 0u);
\t\t\t\t\t\twr(conf.base + 0x54, (uint32_t)PCIE_SMMU_VEC_IOVA);
\t\t\t\t\t\tif (cap & 0x80u) {
\t\t\t\t\t\t\twr(conf.base + 0x58, 0u);
\t\t\t\t\t\t}
\t\t\t\t\t\twr(conf.base + doff, 0x00005a5au);
\t\t\t\t\t\twr(conf.base + 0x50, (cap & 0xffff0000u) |
\t\t\t\t\t\t    ((cap & 0xfffeu) | 1u));
\t\t\t\t\t\tprintf("pcie: 5:   21: apply-246 msi armed: cap 0x%08x addr 0x%08x data 0x%08x target 0x%llx\\n",
\t\t\t\t\t\t    rd(conf.base + 0x50), rd(conf.base + 0x54),
\t\t\t\t\t\t    rd(conf.base + doff),
\t\t\t\t\t\t    (unsigned long long)PCIE_SMMU_VEC_IOVA);
\t\t\t\t\t}
\t\t\t\t}
\t\t\t\twr(bar0.base + 0x118, db);
"""
a1 = "wr(bar0.base + 0x118, db);\n"
assert s.count(a1) == 1, s.count(a1)
s = s.replace(a1, arm)

done = "\t\t\t\t\t\t    rd(bar0.base + 0x13c));\n"
assert s.count(done) == 1, s.count(done)
back = done + """\t\t\t\t\t\t/*
\t\t\t\t\t\t * apply-246: did the msi arrive?  Anything other
\t\t\t\t\t\t * than the marker says the endpoint wrote here.
\t\t\t\t\t\t */
\t\t\t\t\t\tif (pcie_msi_test != 0 && smmu_state == 1 &&
\t\t\t\t\t\t    pcie_dma_vec_pa != 0) {
\t\t\t\t\t\t\tvm_offset_t mv = ml_io_map_unmappable(
\t\t\t\t\t\t\t    (vm_offset_t)pcie_dma_vec_pa, PAGE_SIZE,
\t\t\t\t\t\t\t    VM_WIMG_IO);
\t\t\t\t\t\t\tuint32_t k, hits = 0, first = 0xffffffffu;

\t\t\t\t\t\t\tif (mv != 0) {
\t\t\t\t\t\t\t\t__asm__ __volatile__("dsb sy" ::: "memory");
\t\t\t\t\t\t\t\tfor (k = 0; k < 4096; k += 4) {
\t\t\t\t\t\t\t\t\tuint32_t v = rd(mv + k);

\t\t\t\t\t\t\t\t\tif (v != 0xa5a5a5a5u) {
\t\t\t\t\t\t\t\t\t\tif (hits == 0) {
\t\t\t\t\t\t\t\t\t\t\tfirst = k;
\t\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t\t\tif (hits < 4) {
\t\t\t\t\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-246 msi page +0x%x = 0x%08x\\n",
\t\t\t\t\t\t\t\t\t\t\t    k, v);
\t\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t\t\thits++;
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-246 msi after bhi: %u words changed, first +0x%x; addr 0x%08x data 0x%08x\\n",
\t\t\t\t\t\t\t\t    hits, first, rd(conf.base + 0x54),
\t\t\t\t\t\t\t\t    rd(conf.base + 0x58));
\t\t\t\t\t\t\t}
\t\t\t\t\t\t}
"""
s = s.replace(done, back)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-246 part 2 done:", before, "->", len(s))