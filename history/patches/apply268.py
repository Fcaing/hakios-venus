import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
start = s.index("\t\t\t\t\t\t\t\tbzero((void *)pcie_dma_extra, 0x8000);")
endmark = "rd(pcie_dma_extra + 20 * 0x30), rd(pcie_dma_extra + 21 * 0x30));"
end = s.index(endmark) + len(endmark)
new = '''\t\t\t\t\t\t\t\tbzero((void *)pcie_dma_extra, 0x8000);
\t\t\t\t\t\t\t\t/*
\t\t\t\t\t\t\t\t * apply-268: the vendor's contexts are __packed __aligned(4),
\t\t\t\t\t\t\t\t * so a u64 right after three u32s sits at 0x0c, not 0x10,
\t\t\t\t\t\t\t\t * and the stride the hardware walks is sizeof() = 0x2c.
\t\t\t\t\t\t\t\t */
\t\t\t\t\t\t\t\tfor (i3 = 0; i3 < 3; i3++) {
\t\t\t\t\t\t\t\t\to3 = 0x2000 + i3 * 0x2c;
\t\t\t\t\t\t\t\t\trb = PCIE_EXTRA_IOVA + 0x4000 + (uint64_t)i3 * 0x1000;
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x00, 0);
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x04, 1u);
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x08, 0);
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x0c, (uint32_t)rb);
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x10, (uint32_t)(rb >> 32));
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x14, 0x1000u);
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x18, 0);
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x1c, (uint32_t)rb);
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x20, (uint32_t)(rb >> 32));
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x24, (uint32_t)rb);
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x28, (uint32_t)(rb >> 32));
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\to3 = 0x2400;
\t\t\t\t\t\t\t\trb = PCIE_EXTRA_IOVA + 0x7000;
\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x00, 0);
\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x04, 0);
\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x08, 0);
\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x0c, (uint32_t)rb);
\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x10, (uint32_t)(rb >> 32));
\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x14, 0x1000u);
\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x18, 0);
\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x1c, (uint32_t)rb);
\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x20, (uint32_t)(rb >> 32));
\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x24, (uint32_t)rb);
\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x28, (uint32_t)(rb >> 32));
\t\t\t\t\t\t\t\t{
\t\t\t\t\t\t\t\t\tstatic const uint32_t chans[6] = { 0, 1, 4, 5, 20, 21 };
\t\t\t\t\t\t\t\t\tstatic const uint32_t dirs[6] = { 1, 2, 1, 2, 1, 2 };

\t\t\t\t\t\t\t\t\tfor (i3 = 0; i3 < 6; i3++) {
\t\t\t\t\t\t\t\t\t\to3 = chans[i3] * 0x2c;
\t\t\t\t\t\t\t\t\t\trb = PCIE_EXTRA_IOVA + 0x8000 + (uint64_t)i3 * 0x1000;
\t\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x00, 1u);
\t\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x04, dirs[i3]);
\t\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x08, 1u);
\t\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x0c, (uint32_t)rb);
\t\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x10, (uint32_t)(rb >> 32));
\t\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x14, 0x200u);
\t\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x18, 0);
\t\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x1c, (uint32_t)rb);
\t\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x20, (uint32_t)(rb >> 32));
\t\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x24, (uint32_t)rb);
\t\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x28, (uint32_t)(rb >> 32));
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\tfor (k3 = 0; k3 < 0x8000; k3 += 64) {
\t\t\t\t\t\t\t\t\t__asm__ __volatile__("dc civac, %0" :: "r"(pcie_dma_extra + k3) : "memory");
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t__asm__ __volatile__("dsb sy" ::: "memory");
\t\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-268 er0 rbase 0x%08x rlen 0x%08x rp 0x%08x type 0x%08x ch20 0x%08x ch21 0x%08x\\n",
\t\t\t\t\t\t\t\t    rd(pcie_dma_extra + 0x200c), rd(pcie_dma_extra + 0x2014),
\t\t\t\t\t\t\t\t    rd(pcie_dma_extra + 0x201c), rd(pcie_dma_extra + 0x2004),
\t\t\t\t\t\t\t\t    rd(pcie_dma_extra + 20 * 0x2c), rd(pcie_dma_extra + 21 * 0x2c));'''
s = s[:start] + new + s[end:]
io.open(p, "w", encoding="utf-8").write(s)
print("ok", len(s))