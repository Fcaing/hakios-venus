# -*- coding: utf-8 -*-
import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
anchor = "\t\t\t\t\t/* apply-302: the DT marks ch20/ch21 as mhi,auto-start, so the\n"
assert s.count(anchor) == 1, s.count(anchor)
block = '''\t\t\t\t\t/* apply-308: the vendor only writes the channel contexts once
\t\t\t\t\t * the device is in mission mode (mhi_prepare_for_transfer is
\t\t\t\t\t * called from the user space open of the mhi_uci node).  We wrote
\t\t\t\t\t * them while the device was still in SBL, and the device then
\t\t\t\t\t * overwrote ch20's rp with 0x1:0x1 and never consumed a TRE.
\t\t\t\t\t * Rebuild them here, in mission mode, and ring the er bells. */
\t\t\t\t\tif (pcie_chanstart != 0 && smmu_state == 1 && pcie_dma_extra != 0 &&
\t\t\t\t\t    rd(bar0.base + 0x128) == 2u) {
\t\t\t\t\t\tuint32_t i8, o8;
\t\t\t\t\t\tuint64_t rb8;

\t\t\t\t\t\tfor (i8 = 0; i8 < 0x100; i8 += 4) {
\t\t\t\t\t\t\twr(pcie_dma_extra + i8, 0);
\t\t\t\t\t\t}
\t\t\t\t\t\tfor (i8 = 0x2000; i8 < 0x2480; i8 += 4) {
\t\t\t\t\t\t\twr(pcie_dma_extra + i8, 0);
\t\t\t\t\t\t}
\t\t\t\t\t\tfor (i8 = 0; i8 < 3; i8++) {
\t\t\t\t\t\t\to8 = 0x2000 + i8 * 0x2c;
\t\t\t\t\t\t\trb8 = PCIE_EXTRA_IOVA + 0x4000 + (uint64_t)i8 * 0x1000;
\t\t\t\t\t\t\twr(pcie_dma_extra + o8 + 0x04, 1u);
\t\t\t\t\t\t\twr(pcie_dma_extra + o8 + 0x0c, (uint32_t)rb8);
\t\t\t\t\t\t\twr(pcie_dma_extra + o8 + 0x14, 0x1000u);
\t\t\t\t\t\t\twr(pcie_dma_extra + o8 + 0x1c, (uint32_t)rb8);
\t\t\t\t\t\t\twr(pcie_dma_extra + o8 + 0x24, (uint32_t)(rb8 + 0xff0u));
\t\t\t\t\t\t}
\t\t\t\t\t\to8 = 0x2400;
\t\t\t\t\t\trb8 = PCIE_EXTRA_IOVA + 0x7000;
\t\t\t\t\t\twr(pcie_dma_extra + o8 + 0x0c, (uint32_t)rb8);
\t\t\t\t\t\twr(pcie_dma_extra + o8 + 0x14, 0x1000u);
\t\t\t\t\t\twr(pcie_dma_extra + o8 + 0x1c, (uint32_t)rb8);
\t\t\t\t\t\twr(pcie_dma_extra + o8 + 0x24, (uint32_t)rb8);
\t\t\t\t\t\t{
\t\t\t\t\t\t\tstatic const uint32_t chans8[6] = { 0, 1, 4, 5, 20, 21 };
\t\t\t\t\t\t\tstatic const uint32_t dirs8[6] = { 1, 2, 1, 2, 1, 2 };

\t\t\t\t\t\t\tfor (i8 = 0; i8 < 6; i8++) {
\t\t\t\t\t\t\t\to8 = chans8[i8] * 0x2c;
\t\t\t\t\t\t\t\trb8 = PCIE_EXTRA_IOVA + 0x8000 + (uint64_t)i8 * 0x1000;
\t\t\t\t\t\t\t\twr(pcie_dma_extra + o8 + 0x00, 1u | (2u << 8));
\t\t\t\t\t\t\t\twr(pcie_dma_extra + o8 + 0x04, dirs8[i8]);
\t\t\t\t\t\t\t\twr(pcie_dma_extra + o8 + 0x08, pcie_eridx);
\t\t\t\t\t\t\t\twr(pcie_dma_extra + o8 + 0x0c, (uint32_t)rb8);
\t\t\t\t\t\t\t\twr(pcie_dma_extra + o8 + 0x14, 0x200u);
\t\t\t\t\t\t\t\twr(pcie_dma_extra + o8 + 0x1c, (uint32_t)rb8);
\t\t\t\t\t\t\t\twr(pcie_dma_extra + o8 + 0x24, (uint32_t)rb8);
\t\t\t\t\t\t\t}
\t\t\t\t\t\t}
\t\t\t\t\t\tfor (i8 = 0; i8 < 0x2500; i8 += 64) {
\t\t\t\t\t\t\t__asm__ __volatile__("dc civac, %0" :: "r"(pcie_dma_extra + i8) : "memory");
\t\t\t\t\t\t}
\t\t\t\t\t\t__asm__ __volatile__("dsb sy" ::: "memory");
\t\t\t\t\t\tprintf("pcie: 5:   21: apply-308 rebuilt in mission: ee 0x%08x mh 0x%08x er0 rbase 0x%08x rp 0x%08x ch20 0x%08x rp 0x%08x\\n",
\t\t\t\t\t\t    rd(bar0.base + 0x128), rd(bar0.base + 0x48),
\t\t\t\t\t\t    rd(pcie_dma_extra + 0x200c), rd(pcie_dma_extra + 0x201c),
\t\t\t\t\t\t    rd(pcie_dma_extra + 20 * 0x2c), rd(pcie_dma_extra + 20 * 0x2c + 0x1c));
\t\t\t\t\t\twr(bar0.base + 0x700, (uint32_t)(PCIE_EXTRA_IOVA + 0x4000 + 0xff0));
\t\t\t\t\t\twr(bar0.base + 0x708, (uint32_t)(PCIE_EXTRA_IOVA + 0x5000 + 0xff0));
\t\t\t\t\t\twr(bar0.base + 0x710, (uint32_t)(PCIE_EXTRA_IOVA + 0x6000 + 0xff0));
\t\t\t\t\t}
'''
s = s.replace(anchor, block + anchor)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-308 inserted, %d -> %d bytes" % (len(anchor), len(block)))