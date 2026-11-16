import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
n = len(s)

# arm: write the marker through the cached alias so the clean below really owns the page
a = """\t\t\t\t\tvm_offset_t mv = ml_io_map_unmappable(
\t\t\t\t\t    (vm_offset_t)pcie_dma_vec_pa, PAGE_SIZE, VM_WIMG_IO);
\t\t\t\t\tuint32_t cap = rd(conf.base + 0x50);"""
assert s.count(a) == 1
s = s.replace(a, """\t\t\t\t\t/*
\t\t\t\t\t * apply-247: p247 showed the marker only survived in the
\t\t\t\t\t * three cache lines apply-222 had already cleaned, so the
\t\t\t\t\t * rest of the page was being written back from the stale
\t\t\t\t\t * dirty lines kmem_alloc left behind.  Own the whole page
\t\t\t\t\t * through the cached alias and clean it: after this the
\t\t\t\t\t * only writer to that memory is the endpoint.
\t\t\t\t\t */
\t\t\t\t\tvm_offset_t mv = pcie_dma_vec;
\t\t\t\t\tuint32_t cap = rd(conf.base + 0x50);""")

# readback: invalidate the cached alias first, then read it
b = """\t\t\t\t\t\t\tvm_offset_t mv = ml_io_map_unmappable(
\t\t\t\t\t\t\t    (vm_offset_t)pcie_dma_vec_pa, PAGE_SIZE,
\t\t\t\t\t\t\t    VM_WIMG_IO);
\t\t\t\t\t\t\tuint32_t k, hits = 0, first = 0xffffffffu;"""
assert s.count(b) == 1
s = s.replace(b, """\t\t\t\t\t\t\tvm_offset_t mv = pcie_dma_vec;
\t\t\t\t\t\t\tuint32_t k, hits = 0, first = 0xffffffffu;""")

c = """\t\t\t\t\t\t\tif (mv != 0) {
\t\t\t\t\t\t\t\t__asm__ __volatile__("dsb sy" ::: "memory");
\t\t\t\t\t\t\t\tfor (k = 0; k < 4096; k += 4) {"""
assert s.count(c) == 1
s = s.replace(c, """\t\t\t\t\t\t\tif (mv != 0) {
\t\t\t\t\t\t\t\tfor (k = 0; k < 4096; k += 64) {
\t\t\t\t\t\t\t\t\t__asm__ __volatile__("dc ivac, %0"
\t\t\t\t\t\t\t\t\t    :: "r"(mv + (vm_offset_t)k) : "memory");
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t__asm__ __volatile__("dsb sy" ::: "memory");
\t\t\t\t\t\t\t\tfor (k = 0; k < 4096; k += 4) {""")

io.open(p, "w", encoding="utf-8").write(s)
print("apply-247:", n, "->", len(s))