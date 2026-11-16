import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
n0 = len(s)

# 1. er context: rp = rbase, wp = rbase + len - el_size (vendor ring->wp)
old = """\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x1c, (uint32_t)rb);
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x20, (uint32_t)(rb >> 32));
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x24, (uint32_t)rb);
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x28, (uint32_t)(rb >> 32));
\t\t\t\t\t\t\t\t}"""
new = """\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x1c, (uint32_t)rb);
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x20, (uint32_t)(rb >> 32));
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x24, (uint32_t)(rb + 0xff0u));
\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x28, (uint32_t)(rb >> 32));
\t\t\t\t\t\t\t\t\t/* apply-269: the vendor leaves er wp at the last element */
\t\t\t\t\t\t\t\t}"""
assert s.count(old) == 1, "a1"
s = s.replace(old, new)

# 2. wake db + er doorbell value + mhicfg read-modify-write
anchor = """\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-264 before init: mh 0x%08x ee 0x%08x cfg 0x%08x ctrl 0x%08x\\n","""
assert s.count(anchor) == 1, "a2"
s = s.replace(anchor, """\t\t\t\t\t\t\t/* apply-269: the vendor clears the device wake doorbell first */
\t\t\t\t\t\t\tif (pcie_mhi_nobase == 0 && chdboff != 0) {
\t\t\t\t\t\t\t\twr(bar0.base + chdboff + 8u * 127u, 0);
\t\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-269 wake db 0x%08x = 0x%08x\\n",
\t\t\t\t\t\t\t\t    chdboff + 8u * 127u, rd(bar0.base + chdboff + 8u * 127u));
\t\t\t\t\t\t\t}
""" + anchor)

old2 = """\t\t\t\t\t\t\t\tif (nocfg == 0) {
\t\t\t\t\t\t\t\t\twr(bar0.base + 0x10, 0x00030880u);"""
new2 = """\t\t\t\t\t\t\t\tif (nocfg == 0) {
\t\t\t\t\t\t\t\t\tuint32_t cf = rd(bar0.base + 0x10);

\t\t\t\t\t\t\t\t\t/* apply-269: only ner/nhwer are host writable */
\t\t\t\t\t\t\t\t\twr(bar0.base + 0x10, (cf & ~0xff000000u) | (2u << 24) | (3u << 16));
\t\t\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-269 mhicfg 0x%08x -> 0x%08x\\n",
\t\t\t\t\t\t\t\t\t    cf, rd(bar0.base + 0x10));"""
assert s.count(old2) == 1, "a3"
s = s.replace(old2, new2)

io.open(p, "w", encoding="utf-8").write(s)
print("ok", n0, "->", len(s))