p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
src = open(p).read()

anchor1 = "void\nhakios_pcie_stage(void)\n"
assert src.count(anchor1) == 1, ("anchor1", src.count(anchor1))

helper = """static uint32_t
pcie_crc32(const uint8_t *p, uint32_t n)
{
\tuint32_t crc = 0xffffffffu;
\tuint32_t i;
\tint b;

\tfor (i = 0; i < n; i++) {
\t\tcrc ^= p[i];
\t\tfor (b = 0; b < 8; b++) {
\t\t\tcrc = (crc >> 1) ^ (0xedb88320u & (0u - (crc & 1u)));
\t\t}
\t}
\treturn ~crc;
}

"""

anchor2 = """\t\t\tprintf("pcie: stage: the SBL segment is now an infinite loop\\n");
\t\t}
\t}
\tpcie_fw_size = fsize;
"""
assert src.count(anchor2) == 1, ("anchor2", src.count(anchor2))

repl2 = """\t\t\tprintf("pcie: stage: the SBL segment is now an infinite loop\\n");
\t\t}
\t}
\t/*
\t * apply-238: every probe above writes into the staging page AFTER the
\t * first cache flush, so those bytes may never reach the DDR the
\t * endpoint DMAs from.  Flush again, and print a checksum of exactly
\t * what the endpoint will read.
\t */
\tfor (i = 0; i < n; i += 64) {
\t\t__asm__ volatile ("dc civac, %0" : : "r" (pcie_dma + i) : "memory");
\t}
\t__asm__ volatile ("dsb sy" : : : "memory");
\tprintf("pcie: stage: apply-238 flushed again, crc32 0x%08x over %u bytes, first word 0x%08x\\n",
\t       pcie_crc32((const uint8_t *)pcie_dma, n), n, rd(pcie_dma));
\tpcie_fw_size = fsize;
"""

src = src.replace(anchor1, helper + anchor1, 1)
src = src.replace(anchor2, repl2, 1)
open(p, "w").write(src)
print("patched, file is now", len(src), "bytes")