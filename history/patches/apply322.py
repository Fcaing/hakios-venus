import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

start_marker = "/* apply-311: prime the receive ring the way mhi_queue_inbound()"
end_marker = "rd(pcie_dma_extra + 0x201c));"
i = s.index(start_marker)
j = s.index(end_marker) + len(end_marker)

T = "\t\t\t\t\t\t"
new = (
T + "/* apply-322: prime the WHOLE receive ring.  The vendor's mhi_queue_inbound()\n"
+ T + " * fills all 32 entries of ch21 with 0x8000 buffers before any traffic;\n"
+ T + " * we had only ever queued two, so the device may be waiting for a full ring.\n"
+ T + " */\n"
+ T + "for (d31 = 0; d31 < 32u; d31++) {\n"
+ T + "\twr(pcie_dma_extra + 0xd000 + d31 * 0x10 + 0x00,\n"
+ T + "\t    (uint32_t)(PCIE_EXTRA_IOVA + 0x300000u + d31 * 0x8000u));\n"
+ T + "\twr(pcie_dma_extra + 0xd000 + d31 * 0x10 + 0x04, 0u);\n"
+ T + "\twr(pcie_dma_extra + 0xd000 + d31 * 0x10 + 0x08, 0x00008000u);\n"
+ T + "\twr(pcie_dma_extra + 0xd000 + d31 * 0x10 + 0x0c, 0x00020200u);\n"
+ T + "}\n"
+ T + "wr(pcie_dma_extra + 21 * 0x2c + 0x24, (uint32_t)(PCIE_EXTRA_IOVA + 0xd200));\n"
+ T + "wr(pcie_dma_extra + 21 * 0x2c + 0x28, 0u);\n"
+ T + "for (d31 = 0; d31 < 0x2000; d31 += 64) {\n"
+ T + "\t__asm__ volatile (\"dc ivac, %0\" : : \"r\" (pcie_dma_extra + 0xd000 + d31) : \"memory\");\n"
+ T + "}\n"
+ T + "__asm__ volatile (\"dsb sy\" : : : \"memory\");\n"
+ T + "printf(\"pcie: 5:   21: apply-322 rx primed 32: rx[0] %08x %08x %08x %08x rx[1f0] %08x %08x ch21 wp 0x%08x\\n\",\n"
+ T + "\t    rd(pcie_dma_extra + 0xd000), rd(pcie_dma_extra + 0xd004),\n"
+ T + "\t    rd(pcie_dma_extra + 0xd008), rd(pcie_dma_extra + 0xd00c),\n"
+ T + "\t    rd(pcie_dma_extra + 0xd1f0), rd(pcie_dma_extra + 0xd1f4),\n"
+ T + "\t    rd(pcie_dma_extra + 21 * 0x2c + 0x24));\n"
+ T + "wr(bar0.base + 0x300 + 21 * 8, (uint32_t)(PCIE_EXTRA_IOVA + 0xd200));\n"
+ T + "sleep_ms(20);\n"
+ T + "printf(\"pcie: 5:   21: apply-322 after the rx bell: ch21 rp 0x%08x wp 0x%08x buf0 %08x er0 rp 0x%08x\\n\",\n"
+ T + "\t    rd(pcie_dma_extra + 21 * 0x2c + 0x1c), rd(pcie_dma_extra + 21 * 0x2c + 0x24),\n"
+ T + "\t    rd(pcie_dma_extra + 0xe000), rd(pcie_dma_extra + 0x201c));"
)
s = s[:i] + new + s[j:]
io.open(p, "w", encoding="utf-8").write(s)
print("apply-322 block written")