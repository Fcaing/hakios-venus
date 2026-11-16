import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

# 1) statics for the deferred print
anchor = "static uint32_t pcie_chanlate;"
assert s.count(anchor) == 1
s = s.replace(anchor, "static uint32_t bw_seq, bw_rp0, bw_rp1, bw_ok, bw_ms;	/* apply-327: deferred bw report */\n" + anchor)

# 2) record instead of only printing
old = '\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-326 bw req after %u ms rp 0x%08x ev %08x %08x %08x %08x seq %u\\n",\n\t\t\t\t\t\t\t    i26, rp26, e0, e1, e2, e3, seq);'
assert s.count(old) == 1
new = ('\t\t\t\t\t\t\tbw_ms = i26; bw_rp0 = eb26; bw_rp1 = rp26; bw_seq = seq; bw_ok = 1u;\n'
       '\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-326 bw req after %u ms rp 0x%08x ev %08x %08x %08x %08x seq %u\\n",\n'
       '\t\t\t\t\t\t\t    i26, rp26, e0, e1, e2, e3, seq);')
s = s.replace(old, new)

# 3) deferred tail print before the final apply-225 line
tail = 'printf("pcie: 5:   21: apply-225 final:'
assert s.count(tail) == 1
i = s.rindex("\n", 0, s.index(tail))
T = "\t\t\t\t\t"
add = ("\n" + T + "__asm__ volatile (\"dc ivac, %0\" : : \"r\" (pcie_dma_extra + 20 * 0x2c + 0x1c) : \"memory\");\n"
 + T + "__asm__ volatile (\"dsb sy\" : : : \"memory\");\n"
 + T + "printf(\"pcie: 5:   21: apply-327 tail: bw ok %u seq %u rp0 0x%08x rp1 0x%08x ch20 rp 0x%08x wp 0x%08x ee 0x%08x mh 0x%08x\\n\",\n"
 + T + "    bw_ok, bw_seq, bw_rp0, bw_rp1,\n"
 + T + "    *(volatile uint32_t *)(pcie_dma_extra + 20 * 0x2c + 0x1c),\n"
 + T + "    *(volatile uint32_t *)(pcie_dma_extra + 20 * 0x2c + 0x24),\n"
 + T + "    rd(bar0.base + 0x128), rd(bar0.base + 0x48));\n")
s = s[:i] + add + s[i:]
io.open(p, "w", encoding="utf-8").write(s)
print("apply-327 tail print added")