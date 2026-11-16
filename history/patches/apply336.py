import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
lines = io.open(p, encoding="utf-8").read().split("\n")
# find the closing of the apply-252 done printf statement (ends with ');')
idx = None
for i, l in enumerate(lines):
    if "apply-252 done ee 0x%08x" in l:
        idx = i
        break
assert idx is not None
j = idx
while ");" not in lines[j]:
    j += 1
indent = lines[idx][:len(lines[idx]) - len(lines[idx].lstrip("\t"))]
T = indent
P = T + "\t"
block = [T + "/* apply-336: follow mhi_uci exactly - the vendor only initialises a",
         T + " * channel context, starts the channel and queues buffers once the",
         T + " * device has announced MISSION mode.  Position is an iova: offsets",
         T + " * into pcie_dma_extra are plain offsets, never dring values. */",
         T + "if (pcie_mhi_data == 2u && smmu_state == 1 && pcie_dma_extra != 0) {",
         P + "uint32_t c36 = 20u * 0x2c, r36 = 0xc000u, t36, done36 = 0;",
         P + "uint64_t rb36 = PCIE_EXTRA_IOVA + r36, cw36;",
         P + "printf(\"apply-336 mission ctx: before %08x %08x %08x %08x %08x %08x %08x %08x\\n\",",
         P + "    rd(pcie_dma_extra + c36 + 0x00), rd(pcie_dma_extra + c36 + 0x04), rd(pcie_dma_extra + c36 + 0x08), rd(pcie_dma_extra + c36 + 0x0c),",
         P + "    rd(pcie_dma_extra + c36 + 0x14), rd(pcie_dma_extra + c36 + 0x1c), rd(pcie_dma_extra + c36 + 0x24), rd(bar0.base + 0x48));",
         P + "wr(pcie_dma_extra + c36 + 0x00, 1u);\t\t/* chstate = enabled */",
         P + "wr(pcie_dma_extra + c36 + 0x04, 1u);\t\t/* chtype = tx */",
         P + "wr(pcie_dma_extra + c36 + 0x08, 1u);\t\t/* event ring 1 */",
         P + "wr(pcie_dma_extra + c36 + 0x0c, (uint32_t)rb36);",
         P + "wr(pcie_dma_extra + c36 + 0x10, 0u);",
         P + "wr(pcie_dma_extra + c36 + 0x14, 0x200u);",
         P + "wr(pcie_dma_extra + c36 + 0x18, 0u);",
         P + "wr(pcie_dma_extra + c36 + 0x1c, (uint32_t)rb36);",
         P + "wr(pcie_dma_extra + c36 + 0x20, 0u);",
         P + "wr(pcie_dma_extra + c36 + 0x24, (uint32_t)rb36);",
         P + "wr(pcie_dma_extra + c36 + 0x28, 0u);",
         P + "__asm__ volatile (\"dsb sy\" : : : \"memory\");",
         P + "printf(\"apply-336 mission ctx: after %08x %08x %08x %08x rp %08x wp %08x\\n\",",
         P + "    rd(pcie_dma_extra + c36 + 0x00), rd(pcie_dma_extra + c36 + 0x04), rd(pcie_dma_extra + c36 + 0x08), rd(pcie_dma_extra + c36 + 0x0c),",
         P + "    rd(pcie_dma_extra + c36 + 0x1c), rd(pcie_dma_extra + c36 + 0x24));",
         P + "wr(bar0.base + 0x300 + 8u * 127u, 1u);",
         P + "wr(bar0.base + 0x300 + 8u * 127u, 0u);",
         P + "wr(pcie_dma_extra + 0x7000u, 0x14120000u);\t/* start chan 20 */",
         P + "cw36 = PCIE_EXTRA_IOVA + 0x7010u;",
         P + "wr(pcie_dma_extra + 0x2400u + 0x1c, (uint32_t)(PCIE_EXTRA_IOVA + 0x7000u));",
         P + "wr(pcie_dma_extra + 0x2400u + 0x24, (uint32_t)cw36);",
         P + "wr(pcie_dma_extra + 0x2400u + 0x28, 0u);",
         P + "__asm__ volatile (\"dsb sy\" : : : \"memory\");",
         P + "wr(bar0.base + 0x70, (uint32_t)cw36);",
         P + "for (t36 = 0; t36 < 60u; t36++) {",
         P + "\tsleep_ms(5);",
         P + "\tif (rd(pcie_dma_extra + 0x201cu) != (uint32_t)rb) { done36 = 1; break; }",
         P + "}",
         P + "printf(\"apply-336 start: er0 rp %08x (was %08x) after %u ms, mh %08x ee %08x\\n\",",
         P + "    rd(pcie_dma_extra + 0x201cu), (uint32_t)rb, t36 * 5, rd(bar0.base + 0x48), rd(bar0.base + 0x128));",
         P + "}"
        ]
lines = lines[:j+1] + block + lines[j+1:]
io.open(p, "w", encoding="utf-8").write("\n".join(lines))
print("apply-336 inserted")