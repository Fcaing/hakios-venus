import io
p="/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s=io.open(p,encoding="utf-8",errors="surrogateescape").read()
a='''									wr(pcie_dma_extra + o3 + 0x24, (uint32_t)(rb + 0xff0u));
									wr(pcie_dma_extra + o3 + 0x28, (uint32_t)(rb >> 32));
									/* apply-269: the vendor leaves er wp at the last element */'''
n='''									/* apply-358: an event ring starts empty: rp == wp == rbase.
									 * apply-269 parked wp on the last element, which left every
									 * ring one slot from full -- the device then wrote two events
									 * and went silent, and we spent days reading zeros. */
									wr(pcie_dma_extra + o3 + 0x24, (uint32_t)rb);
									wr(pcie_dma_extra + o3 + 0x28, (uint32_t)(rb >> 32));'''
assert s.count(a)==1, s.count(a)
s=s.replace(a,n)
io.open(p,"w",encoding="utf-8",errors="surrogateescape").write(s)
print("apply-358 ok")