import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
T = "\t" * 6

old_trewp = T + "uint64_t trewp = dring + 0x10;"
assert s.count(old_trewp) == 1, s.count(old_trewp)
s = s.replace(old_trewp, T + "uint64_t trewp = dring + 0x20;")

old = (
    T + "wr(pcie_dma_extra + dring_off + 0x0000, (uint32_t)datiova);\n"
    + T + "wr(pcie_dma_extra + dring_off + 0x0004, (uint32_t)(datiova >> 32));\n"
    + T + "wr(pcie_dma_extra + dring_off + 0x0008, 0x40u);\n"
    + T + "wr(pcie_dma_extra + dring_off + 0x000c, 0x00020200u);\n"
)
assert s.count(old) == 1, s.count(old)
new = (
    T + "/* apply-313: two page sized transfers instead of one 64 byte one, and\n"
    + T + " * the buffers live in the region the rx ring was just primed with.\n"
    + T + " */\n"
    + T + "wr(pcie_dma_extra + dring_off + 0x0000, (uint32_t)(PCIE_EXTRA_IOVA + 0xe000u));\n"
    + T + "wr(pcie_dma_extra + dring_off + 0x0004, 0u);\n"
    + T + "wr(pcie_dma_extra + dring_off + 0x0008, 0x00001000u);\n"
    + T + "wr(pcie_dma_extra + dring_off + 0x000c, 0x00020200u);\n"
    + T + "wr(pcie_dma_extra + dring_off + 0x0010, (uint32_t)(PCIE_EXTRA_IOVA + 0xf000u));\n"
    + T + "wr(pcie_dma_extra + dring_off + 0x0014, 0u);\n"
    + T + "wr(pcie_dma_extra + dring_off + 0x0018, 0x00001000u);\n"
    + T + "wr(pcie_dma_extra + dring_off + 0x001c, 0x00020200u);\n"
)
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-313 written")