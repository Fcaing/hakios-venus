import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
s = s.replace("if (rd(pcie_dma_extra + 0x201cu) != (uint32_t)rb) { done36 = 1; break; }",
              "if (rd(pcie_dma_extra + 0x201cu) != (uint32_t)rb36) { done36 = 1; break; }", 1)
s = s.replace("      rd(pcie_dma_extra + 0x201cu), (uint32_t)rb, t36 * 5, rd(bar0.base + 0x48), rd(bar0.base + 0x128));",
              "      rd(pcie_dma_extra + 0x201cu), (uint32_t)rb36, t36 * 5, rd(bar0.base + 0x48), rd(bar0.base + 0x128));", 1)
io.open(p, "w", encoding="utf-8").write(s)
print("fixed rb refs")