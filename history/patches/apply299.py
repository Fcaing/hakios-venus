import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
old = "wr(pcie_dma_extra + o3 + 0x00, 1u);"
assert s.count(old) == 1, s.count(old)
new = ("/* apply-299: vendor defaults brstmode to MHI_BRSTMODE_ENABLE(3) when the\n"
       "\t\t\t\t\t\t\t * DT has no mhi,brstmode; we wrote 0, which MHI calls\n"
       "\t\t\t\t\t\t\t * MHI_INVALID_BRSTMODE.  chstate=1 | brstmode=3<<8. */\n"
       "\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x00, 1u | (3u << 8));")
s = s.replace(old, new)
s = s.replace('printf("pcie: 5:   21: apply-268 er0 rbase', 'printf("pcie: 5:   21: apply-299 er0 rbase')
io.open(p, "w", encoding="utf-8").write(s)
print("patched")