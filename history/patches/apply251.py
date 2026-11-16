import io
path = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
src = io.open(path, encoding="utf-8").read()

a0 = "static uint32_t pcie_msi_test;\t\t/* apply-246: point the endpoint's msi at our own page */\n"
assert src.count(a0) == 1, src.count(a0)
src = src.replace(a0, a0 + "static uint32_t pcie_mhi_init = 1;\t/* apply-251: program the mhi mmio and ask for m0 */\n")

a1 = "\t\t\t\t\t/*\n\t\t\t\t\t * apply-240: star's stage 11 programs the bus number\n"
assert src.count(a1) == 1, src.count(a1)

block = """\t\t\t\t\t/*
\t\t\t\t\t * apply-251: the vendor programs the mhi mmio and asks for
\t\t\t\t\t * m0 the moment the device reports READY, before handing
\t\t\t\t\t * over the rest of the image.  The SBL wipes whatever we
\t\t\t\t\t * wrote before BHI, so the whole block repeats here.
\t\t\t\t\t */
\t\t\t\t\t{
\t\t\t\t\t\tuint32_t want = pcie_mhi_init;
\t\t\t\t\t\tuint32_t chdboff, erdboff, k3;
\t\t\t\t\t\tuint64_t ctxt = PCIE_EXTRA_IOVA;
\t\t\t\t\t\tuint64_t erct = PCIE_EXTRA_IOVA + 0x800;
\t\t\t\t\t\tuint64_t crct = PCIE_EXTRA_IOVA + 0xc00;
\t\t\t\t\t\tuint64_t lo = 0xa0000000ull, hi = 0xb0000000ull;

\t\t\t\t\t\tPE_parse_boot_argn("pcie_mhi_init", &want, sizeof(want));
\t\t\t\t\t\tif (want != 0) {
\t\t\t\t\t\t\tchdboff = rd(bar0.base + 0x18);
\t\t\t\t\t\t\terdboff = rd(bar0.base + 0x20);
\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-251 mhi init: chdboff 0x%x erdboff 0x%x ee 0x%08x mh 0x%08x\\n",
\t\t\t\t\t\t\t    chdboff, erdboff, rd(bar0.base + 0x128), rd(bar0.base + 0x48));
\t\t\t\t\t\t\tif (pcie_dma_extra != 0) {
\t\t\t\t\t\t\t\tbzero((void *)pcie_dma_extra, 0x2000);
\t\t\t\t\t\t\t\tfor (k3 = 0; k3 < 0x2000; k3 += 64) {
\t\t\t\t\t\t\t\t\t__asm__ __volatile__("dc civac, %0" :: "r"(pcie_dma_extra + k3) : "memory");
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t__asm__ __volatile__("dsb sy" ::: "memory");
\t\t\t\t\t\t\twr(bar0.base + 0x5c, (uint32_t)(ctxt >> 32));
\t\t\t\t\t\t\twr(bar0.base + 0x58, (uint32_t)ctxt);
\t\t\t\t\t\t\twr(bar0.base + 0x64, (uint32_t)(erct >> 32));
\t\t\t\t\t\t\twr(bar0.base + 0x60, (uint32_t)erct);
\t\t\t\t\t\t\twr(bar0.base + 0x6c, (uint32_t)(crct >> 32));
\t\t\t\t\t\t\twr(bar0.base + 0x68, (uint32_t)crct);
\t\t\t\t\t\t\twr(bar0.base + 0x10, 0x00030880u);
\t\t\t\t\t\t\twr(bar0.base + 0x84, (uint32_t)(lo >> 32));
\t\t\t\t\t\t\twr(bar0.base + 0x80, (uint32_t)lo);
\t\t\t\t\t\t\twr(bar0.base + 0x88, (uint32_t)hi);
\t\t\t\t\t\t\twr(bar0.base + 0x8c, (uint32_t)(hi >> 32));
\t\t\t\t\t\t\twr(bar0.base + 0x9c, (uint32_t)(lo >> 32));
\t\t\t\t\t\t\twr(bar0.base + 0x98, (uint32_t)lo);
\t\t\t\t\t\t\twr(bar0.base + 0xa0, (uint32_t)hi);
\t\t\t\t\t\t\twr(bar0.base + 0xa4, (uint32_t)(hi >> 32));
\t\t\t\t\t\t\twr(bar0.base + 0x38, (rd(bar0.base + 0x38) & ~0xff00u) | (2u << 8));
\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-251 after init: cfg 0x%08x ccbap 0x%08x ecbap 0x%08x crcbap 0x%08x ctrl 0x%08x mh 0x%08x ee 0x%08x\\n",
\t\t\t\t\t\t\t    rd(bar0.base + 0x10), rd(bar0.base + 0x58), rd(bar0.base + 0x60),
\t\t\t\t\t\t\t    rd(bar0.base + 0x68), rd(bar0.base + 0x38), rd(bar0.base + 0x48),
\t\t\t\t\t\t\t    rd(bar0.base + 0x128));
\t\t\t\t\t\t}
\t\t\t\t\t}
"""
src = src.replace(a1, block + a1)
io.open(path, "w", encoding="utf-8").write(src)
print("apply-251 done", len(src))