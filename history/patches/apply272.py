import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
n0 = len(s)

a = """\t\t\t\t\tif (pcie_mhi_watch != 0 && smmu_state == 1) {"""
assert s.count(a) == 1
s = s.replace(a, """\t\t\t\t\tif (pcie_mhi_watch != 0 && smmu_state == 1 && pcie_dma_extra != 0) {
\t\t\t\t\t\tvolatile uint32_t *ex = (volatile uint32_t *)pcie_dma_extra;""")

a2 = """\t\t\t\t\t\t\tf0 = rd(bar0.base + 0x228);
\t\t\t\t\t\t\tf1 = rd(bar0.base + 0x328);
\t\t\t\t\t\t\tf2 = rd(bar0.base + 0x428);
\t\t\t\t\t\t\tg0 = rd(bar0.base + 0x230);
\t\t\t\t\t\t\tg1 = rd(bar0.base + 0x330);
\t\t\t\t\t\t\tg2 = rd(bar0.base + 0x430);"""
assert s.count(a2) == 1
s = s.replace(a2, """\t\t\t\t\t\t\t__asm__ volatile ("dc ivac, %0" : : "r" ((char *)ex + 0x2000) : "memory");
\t\t\t\t\t\t\t__asm__ volatile ("dsb sy" : : : "memory");
\t\t\t\t\t\t\tf0 = ex[0x2000 / 4 + 7];	/* er0 ctxt wp (0x1c) */
\t\t\t\t\t\t\tf1 = ex[0x3000 / 4 + 7];	/* er1 ctxt wp */
\t\t\t\t\t\t\tf2 = ex[0x4000 / 4 + 7];	/* er2 ctxt wp */
\t\t\t\t\t\t\tg0 = ex[0x1000 / 4];		/* er0 ring tre 0 dword 0 */
\t\t\t\t\t\t\tg1 = ex[0x1004 / 4];
\t\t\t\t\t\t\tg2 = ex[0x1008 / 4];""")

io.open(p, "w", encoding="utf-8").write(s)
print("ok", n0, "->", len(s))