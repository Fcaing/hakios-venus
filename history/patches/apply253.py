import io
path = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
src = io.open(path, encoding="utf-8").read()

a1 = "\t\t\t\t\t\tuint64_t erct = PCIE_EXTRA_IOVA + 0x800;\n"
a2 = "\t\t\t\t\t\tuint64_t crct = PCIE_EXTRA_IOVA + 0xc00;\n"
assert src.count(a1) == 1 and src.count(a2) == 1
src = src.replace(a1, "\t\t\t\t\t\tuint64_t erct = PCIE_EXTRA_IOVA + 0x2000;\n")
src = src.replace(a2, "\t\t\t\t\t\tuint64_t crct = PCIE_EXTRA_IOVA + 0x2400;\n")

old = """\t\t\t\t\t\t\tif (pcie_dma_extra != 0) {
\t\t\t\t\t\t\t\tbzero((void *)pcie_dma_extra, 0x2000);
\t\t\t\t\t\t\t\tfor (k3 = 0; k3 < 0x2000; k3 += 64) {
\t\t\t\t\t\t\t\t\t__asm__ __volatile__("dc civac, %0" :: "r"(pcie_dma_extra + k3) : "memory");
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t}
"""
assert src.count(old) == 1, src.count(old)

new = """\t\t\t\t\t\t\tif (pcie_dma_extra != 0) {
\t\t\t\t\t\t\t\tuint32_t i3, o3;
\t\t\t\t\t\t\t\tuint64_t rb;

\t\t\t\t\t\t\t\tbzero((void *)pcie_dma_extra, 0x8000);
\t\t\t\t\t\t\t\tfor (i3 = 0; i3 < 3; i3++) {
\t\t\t\t\t\t\t\t\to3 = 0x2000 + i3 * 0x30;
\t\t\t\t\t\t\t\t\trb = PCIE_EXTRA_IOVA + 0x4000 + (uint64_t)i3 * 0x1000;
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x00, 0);
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x04, 1u);
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x08, 0);
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x10, (uint32_t)rb);
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x14, (uint32_t)(rb >> 32));
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x18, 0x1000u);
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x1c, 0);
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x20, (uint32_t)rb);
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x24, (uint32_t)(rb >> 32));
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x28, (uint32_t)rb);
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x2c, (uint32_t)(rb >> 32));
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\to3 = 0x2400;
\t\t\t\t\t\t\t\trb = PCIE_EXTRA_IOVA + 0x7000;
\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x10, (uint32_t)rb);
\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x14, (uint32_t)(rb >> 32));
\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x18, 0x1000u);
\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x1c, 0);
\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x20, (uint32_t)rb);
\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x24, (uint32_t)(rb >> 32));
\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x28, (uint32_t)rb);
\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x2c, (uint32_t)(rb >> 32));
\t\t\t\t\t\t\t\tfor (k3 = 0; k3 < 0x8000; k3 += 64) {
\t\t\t\t\t\t\t\t\t__asm__ __volatile__("dc civac, %0" :: "r"(pcie_dma_extra + k3) : "memory");
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t__asm__ __volatile__("dsb sy" ::: "memory");
\t\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-253 er0 rbase 0x%08x rlen 0x%08x rp 0x%08x type 0x%08x cmd rbase 0x%08x\\n",
\t\t\t\t\t\t\t\t    rd(pcie_dma_extra + 0x2010), rd(pcie_dma_extra + 0x2018),
\t\t\t\t\t\t\t\t    rd(pcie_dma_extra + 0x2020), rd(pcie_dma_extra + 0x2004),
\t\t\t\t\t\t\t\t    rd(pcie_dma_extra + 0x2410));
\t\t\t\t\t\t\t}
"""
src = src.replace(old, new)
io.open(path, "w", encoding="utf-8").write(src)
print("apply-253 done", len(src))