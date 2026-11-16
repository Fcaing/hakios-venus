import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
for n in (1, 2):
    for off in ("0x1c", "0x24"):
        old = "rd(pcie_dma_extra + %d * 0x2c + %s)" % (n, off)
        new = "rd(pcie_dma_extra + 0x2000 + %d * 0x2c + %s)" % (n, off)
        cnt = s.count(old)
        assert cnt == 1, (old, cnt)
        s = s.replace(old, new)
s = s.replace("apply-296 t=%u ms", "apply-297 t=%u ms")
io.open(p, "w", encoding="utf-8").write(s)
print("patched", len(s))