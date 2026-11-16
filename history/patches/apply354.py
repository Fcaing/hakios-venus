import io,re
p="/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s=io.open(p,encoding="utf-8",errors="surrogateescape").read()
old='#define PCIE_EXTRA_IOVA     0xa0200000ull'
new='#define PCIE_EXTRA_IOVA     0xa1c00000ull    /* apply-354: try where star keeps its MHI buffers */'
assert s.count(old)==1, s.count(old)
s=s.replace(old,new)
io.open(p,"w",encoding="utf-8",errors="surrogateescape").write(s)
print("apply-354 ok")