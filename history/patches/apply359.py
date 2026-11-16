import io
p="/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s=io.open(p,encoding="utf-8",errors="surrogateescape").read()
a='#define PCIE_EXTRA_IOVA     0xa1c00000ull    /* apply-354: try where star keeps its MHI buffers */'
n='#define PCIE_EXTRA_IOVA     0xa0200000ull	/* apply-359: a/b, back where the ee events did arrive */'
assert s.count(a)==1, s.count(a)
s=s.replace(a,n)
io.open(p,"w",encoding="utf-8",errors="surrogateescape").write(s)
print("apply-359 ok")