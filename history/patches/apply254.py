import io
path = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
src = io.open(path, encoding="utf-8").read()
a = """\t\tprintf("pcie: stage: image 0x%x bytes at 0x%llx (iova 0x%llx), first word 0x%08x\\n",
\t\t       en, (unsigned long long)dst,
\t\t       (unsigned long long)(PCIE_EXTRA_IOVA + PCIE_EXTRA_DATA_OFF), rd(dst));
"""
assert src.count(a) == 1, src.count(a)
add = a + """\t\t/*
\t\t * apply-254: what will the endpoint actually read from this
\t\t * region?  Drop the cache lines first, then checksum exactly
\t\t * the bytes the bhie table points at.
\t\t */
\t\tfor (i = 0; i < en; i += 64) {
\t\t\t__asm__ volatile ("dc ivac, %0" : : "r" (dst + i) : "memory");
\t\t}
\t\t__asm__ volatile ("dsb sy" : : : "memory");
\t\tprintf("pcie: stage: apply-254 the endpoint will read crc32 0x%08x over 0x%x bytes at +0x%x\\n",
\t\t       pcie_crc32((const uint8_t *)dst, en), en, PCIE_EXTRA_DATA_OFF);
"""
src = src.replace(a, add)
io.open(path, "w", encoding="utf-8").write(src)
print("apply-254 done", len(src))