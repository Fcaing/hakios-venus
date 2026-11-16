import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
lines = io.open(p, encoding="utf-8").read().split("\n")
idx = None
for i, l in enumerate(lines):
    if "apply-336 start: er0 rp" in l:
        idx = i
        break
assert idx is not None, "anchor missing"
j = idx
while lines[j].strip() != "}":
    j += 1
T = "\t" * 6
P = T + "\t"
block = [
 T + "/* apply-337: the full mhi_uci order, with the wait actually working.",
 T + " * The context stays as the sbl wrote it (pcie_chanlate=0); here we only",
 T + " * start the channels, wait for the completions to land in er0, and prime",
 T + " * the receive ring so the device has somewhere to write. */",
 T + "if (pcie_mhi_data == 3u && smmu_state == 1 && pcie_dma_extra != 0 &&",
 T + "    rd(bar0.base + 0x128) == 2u) {",
 P + "uint32_t c37 = 21u * 0x2c, r37 = 0xd000u, k37;",
 P + "uint32_t rp37 = rd(pcie_dma_extra + 0x201cu);",
 P + "uint64_t rb37 = PCIE_EXTRA_IOVA + r37, cw37 = PCIE_EXTRA_IOVA + 0x7040u;",
 P + "wr(pcie_dma_extra + 0x7000u, 0x00120000u);",
 P + "wr(pcie_dma_extra + 0x7010u, 0x01120000u);",
 P + "wr(pcie_dma_extra + 0x7020u, 0x14120000u);",
 P + "wr(pcie_dma_extra + 0x7030u, 0x15120000u);",
 P + "wr(pcie_dma_extra + 0x2400u + 0x1c, (uint32_t)(PCIE_EXTRA_IOVA + 0x7000u));",
 P + "wr(pcie_dma_extra + 0x2400u + 0x24, (uint32_t)cw37);",
 P + "wr(pcie_dma_extra + 0x2400u + 0x28, 0u);",
 P + "__asm__ volatile (\"dsb sy\" : : : \"memory\");",
 P + "wr(bar0.base + 0x70, (uint32_t)cw37);",
 P + "printf(\"apply-337 starts sent, er0 rp was 0x%08x\\n\", rp37);",
 P + "for (k37 = 0; k37 < 80u; k37++) {",
 P + "\tsleep_ms(5);",
 P + "\tif (rd(pcie_dma_extra + 0x201cu) != rp37) {",
 P + "\t\tbreak;",
 P + "\t}",
 P + "}",
 P + "printf(\"apply-337 completions after %u ms: er0 rp 0x%08x ch20 0x%08x ch21 0x%08x mh 0x%08x ee 0x%08x\\n\",",
 P + "    k37 * 5, rd(pcie_dma_extra + 0x201cu), rd(pcie_dma_extra + 20u * 0x2c), rd(pcie_dma_extra + c37),",
 P + "    rd(bar0.base + 0x48), rd(bar0.base + 0x128));",
 P + "for (k37 = 0; k37 < 32u; k37++) {",
 P + "\twr(pcie_dma_extra + r37 + k37 * 0x10u + 0x00u, (uint32_t)(PCIE_EXTRA_IOVA + 0x300000u + k37 * 0x8000u));",
 P + "\twr(pcie_dma_extra + r37 + k37 * 0x10u + 0x04u, 0u);",
 P + "\twr(pcie_dma_extra + r37 + k37 * 0x10u + 0x08u, 0x8000u);",
 P + "\twr(pcie_dma_extra + r37 + k37 * 0x10u + 0x0cu, 0x00020200u);",
 P + "}",
 P + "wr(pcie_dma_extra + c37 + 0x1c, (uint32_t)rb37);",
 P + "wr(pcie_dma_extra + c37 + 0x20, 0u);",
 P + "wr(pcie_dma_extra + c37 + 0x24, (uint32_t)(rb37 + 0x200u));",
 P + "wr(pcie_dma_extra + c37 + 0x28, 0u);",
 P + "__asm__ volatile (\"dsb sy\" : : : \"memory\");",
 P + "wr(bar0.base + 0x300u + 21u * 8u + 4u, 0u);",
 P + "wr(bar0.base + 0x300u + 21u * 8u, (uint32_t)(rb37 + 0x200u));",
 P + "printf(\"apply-337 rx primed: ch21 wp 0x%08x rp 0x%08x\\n\", rd(pcie_dma_extra + c37 + 0x24), rd(pcie_dma_extra + c37 + 0x1c));",
 T + "}",
]
lines = lines[:j+1] + block + lines[j+1:]
io.open(p, "w", encoding="utf-8").write("\n".join(lines))
print("apply-337 inserted")