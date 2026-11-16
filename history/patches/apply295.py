import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
anchor = "\t\t\t\t\t\twr(pcie_dma_extra + 0xc000, (uint32_t)datiova);"
assert s.count(anchor) == 1, s.count(anchor)
T = "\t" * 6
new = (T + "/* apply-295: the device leaves rp as 0x00000001_00000001, which is not an\n"
       + T + " * iova at all. Put the read pointer back to the ring base before handing\n"
       + T + " * it a tre, otherwise it has no reason to look at 0xa020c000. */\n"
       + T + "wr(pcie_dma_extra + 20 * 0x2c + 0x1c, (uint32_t)(PCIE_EXTRA_IOVA + 0xc000));\n"
       + T + "wr(pcie_dma_extra + 20 * 0x2c + 0x20, 0u);\n"
       + T + "printf(\"pcie: 5:   21: apply-295 ch20 rp 0x%08x:%08x\\n\",\n"
       + T + "    rd(pcie_dma_extra + 20 * 0x2c + 0x20), rd(pcie_dma_extra + 20 * 0x2c + 0x1c));\n\n")
s = s.replace(anchor, anchor.replace("\t\t\t\t\t\twr(pcie_dma_extra + 0xc000", new + anchor) )
io.open(p, "w", encoding="utf-8").write(s)
print("apply-295 in", len(s))