import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
T = "\t" * 6
anchor = T + 'printf("pcie: 5:   21: apply-292 send: tre ptr 0x%08x len 0x%08x dw1 0x%08x ch20 wp 0x%08x\\n",'
assert s.count(anchor) == 1, s.count(anchor)
block = (
    T + "/* apply-310: read the RX (device to host) ring too: if the firmware\n"
    + T + " * issued a link request, it has to be written there.\n"
    + T + " */\n"
    + T + "for (d31 = 0; d31 < 0x400; d31 += 64) {\n"
    + T + "\t__asm__ volatile (\"dc ivac, %0\" : : \"r\" (pcie_dma_extra + 0xd000 + d31) : \"memory\");\n"
    + T + "\t__asm__ volatile (\"dc ivac, %0\" : : \"r\" (pcie_dma_extra + 0xc000 + d31) : \"memory\");\n"
    + T + "}\n"
    + T + "__asm__ volatile (\"dsb sy\" : : : \"memory\");\n"
    + T + 'printf("pcie: 5:   21: apply-310 ch21 rx rp 0x%08x wp 0x%08x ch20 tx rp 0x%08x wp 0x%08x\\n",\n'
    + T + "\t    rd(pcie_dma_extra + 21 * 0x2c + 0x1c), rd(pcie_dma_extra + 21 * 0x2c + 0x24),\n"
    + T + "\t    rd(pcie_dma_extra + 20 * 0x2c + 0x1c), rd(pcie_dma_extra + 20 * 0x2c + 0x24));\n"
    + T + "for (d31 = 0; d31 < 0x80; d31 += 0x10) {\n"
    + T + '\tprintf("pcie: 5:   21: apply-310 rx[%02x] %08x %08x %08x %08x\\n", d31,\n'
    + T + "\t    rd(pcie_dma_extra + 0xd000 + d31), rd(pcie_dma_extra + 0xd000 + d31 + 4),\n"
    + T + "\t    rd(pcie_dma_extra + 0xd000 + d31 + 8), rd(pcie_dma_extra + 0xd000 + d31 + 12));\n"
    + T + "}\n"
    + T + "for (d31 = 0; d31 < 0x40; d31 += 0x10) {\n"
    + T + '\tprintf("pcie: 5:   21: apply-310 tx[%02x] %08x %08x %08x %08x\\n", d31,\n'
    + T + "\t    rd(pcie_dma_extra + 0xc000 + d31), rd(pcie_dma_extra + 0xc000 + d31 + 4),\n"
    + T + "\t    rd(pcie_dma_extra + 0xc000 + d31 + 8), rd(pcie_dma_extra + 0xc000 + d31 + 12));\n"
    + T + "}\n"
)
s = s.replace(anchor, block + anchor)
old = T + "uint64_t dring = PCIE_EXTRA_IOVA + dring_off;"
assert s.count(old) == 1, s.count(old)
s = s.replace(old, old + "\n" + T + "uint32_t d31;")
io.open(p, "w", encoding="utf-8").write(s)
print("apply-310 written")