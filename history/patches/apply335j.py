import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
assert "dring_off" in s
old = "\t\t\t\t\t\t\tprintf(\"apply-335 e: tre at 0x%llx keeps len %u, packet sits at its head\\n\",\n\t\t\t\t\t\t\t    (unsigned long long)(PCIE_EXTRA_IOVA + 0xe000u), rd(pcie_dma_extra + dring + 0x08u));\n"
assert s.count(old) == 1
new = "\t\t\t\t\t\t\tprintf(\"apply-335 e: tre at 0x%llx keeps len %u, packet sits at its head\\n\",\n\t\t\t\t\t\t\t    (unsigned long long)(PCIE_EXTRA_IOVA + 0xe000u), rd(pcie_dma_extra + dring_off + 0x08u));\n"
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("fixed iova/offset mixup")