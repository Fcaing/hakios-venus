import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
old = "wr(pcie_dma_extra + o3 + 0x00, 1u | (3u << 8));"
assert s.count(old) == 1, s.count(old)
new = ("/* apply-301: DT says mhi,doorbell-mode = <2> for ch20, so\n"
       "\t\t\t\t\t\t\t * brstmode is MHI_BRSTMODE_DISABLE(2), not ENABLE(3). */\n"
       "\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x00, 1u | (2u << 8));")
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("patched")