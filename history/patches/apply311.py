import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
T = "\t" * 6
anchor = T + "uint64_t dring = PCIE_EXTRA_IOVA + dring_off;\n" + T + "uint32_t d31;\n"
assert s.count(anchor) == 1, s.count(anchor)
block = (
    T + "/* apply-311: prime the receive ring the way mhi_queue_inbound()\n"
    + T + " * does it: the device needs empty buffers before it can write.\n"
    + T + " */\n"
    + T + "wr(pcie_dma_extra + 0xd000 + 0x0000, (uint32_t)(PCIE_EXTRA_IOVA + 0xe000));\n"
    + T + "wr(pcie_dma_extra + 0xd000 + 0x0004, 0u);\n"
    + T + "wr(pcie_dma_extra + 0xd000 + 0x0008, 0x00008000u);\n"
    + T + "wr(pcie_dma_extra + 0xd000 + 0x000c, 0x00020200u);\n"
    + T + "wr(pcie_dma_extra + 0xd000 + 0x0010, (uint32_t)(PCIE_EXTRA_IOVA + 0xf000));\n"
    + T + "wr(pcie_dma_extra + 0xd000 + 0x0014, 0u);\n"
    + T + "wr(pcie_dma_extra + 0xd000 + 0x0018, 0x00008000u);\n"
    + T + "wr(pcie_dma_extra + 0xd000 + 0x001c, 0x00020200u);\n"
    + T + "wr(pcie_dma_extra + 21 * 0x2c + 0x24, (uint32_t)(PCIE_EXTRA_IOVA + 0xd020));\n"
    + T + "wr(pcie_dma_extra + 21 * 0x2c + 0x28, 0u);\n"
    + T + "for (d31 = 0; d31 < 0x2000; d31 += 64) {\n"
    + T + "\t__asm__ volatile (\"dc ivac, %0\" : : \"r\" (pcie_dma_extra + 0xd000 + d31) : \"memory\");\n"
    + T + "}\n"
    + T + "__asm__ volatile (\"dsb sy\" : : : \"memory\");\n"
    + T + 'printf("pcie: 5:   21: apply-311 rx primed: rx[0] %08x %08x %08x %08x rx[10] %08x ch21 wp 0x%08x\\n",\n'
    + T + "\t    rd(pcie_dma_extra + 0xd000), rd(pcie_dma_extra + 0xd004),\n"
    + T + "\t    rd(pcie_dma_extra + 0xd008), rd(pcie_dma_extra + 0xd00c),\n"
    + T + "\t    rd(pcie_dma_extra + 0xd010), rd(pcie_dma_extra + 21 * 0x2c + 0x24));\n"
    + T + "wr(bar0.base + 0x300 + 21 * 8, (uint32_t)(PCIE_EXTRA_IOVA + 0xd020));\n"
    + T + "sleep_ms(20);\n"
    + T + 'printf("pcie: 5:   21: apply-311 after the rx bell: ch21 rp 0x%08x wp 0x%08x buf0 %08x buf1 %08x er0 rp 0x%08x\\n",\n'
    + T + "\t    rd(pcie_dma_extra + 21 * 0x2c + 0x1c), rd(pcie_dma_extra + 21 * 0x2c + 0x24),\n"
    + T + "\t    rd(pcie_dma_extra + 0xe000), rd(pcie_dma_extra + 0xf000),\n"
    + T + "\t    rd(pcie_dma_extra + 0x201c));\n"
)
s = s.replace(anchor, anchor + block)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-311 written")