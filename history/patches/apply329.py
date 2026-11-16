import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
lines = s.split("\n")
# 1) drop the old tail print block (7 lines starting with the dc ivac before apply-327 tail printf)
out = []
i = 0
removed = False
while i < len(lines):
    if "apply-327 tail:" in lines[i]:
        # find start: the line with dc ivac two lines above
        j = len(out) - 1
        while j >= 0 and "dc ivac" not in out[j]:
            j -= 1
        if j >= 0:
            del out[j:]
            removed = True
        i += 1
        # skip continuation lines until the one ending with ');'
        while i < len(lines) and not lines[i].rstrip().endswith(");"):
            i += 1
        i += 1
        continue
    out.append(lines[i])
    i += 1
assert removed
lines = out
# 2) insert the definitive tail print before the apply-169 line
idx = None
for k, l in enumerate(lines):
    if "back to the loader (apply-169)" in l:
        idx = k
assert idx is not None
ind = lines[idx][:len(lines[idx]) - len(lines[idx].lstrip())]
blk = [
    ind + "if (pcie_dma_extra != 0) {",
    ind + "\t__asm__ volatile (\"dc ivac, %0\" : : \"r\" (pcie_dma_extra + 20 * 0x2c + 0x1c) : \"memory\");",
    ind + "\t__asm__ volatile (\"dsb sy\" : : : \"memory\");",
    ind + "\tprintf(\"pcie: 5:   21: apply-327 tail: bw ok %u seq %u rp0 0x%08x rp1 0x%08x ch20 rp 0x%08x wp 0x%08x ee 0x%08x mh 0x%08x\\n\",",
    ind + "\t    bw_ok, bw_seq, bw_rp0, bw_rp1,",
    ind + "\t    *(volatile uint32_t *)(pcie_dma_extra + 20 * 0x2c + 0x1c),",
    ind + "\t    *(volatile uint32_t *)(pcie_dma_extra + 20 * 0x2c + 0x24),",
    ind + "\t    rd(bar0.base + 0x128), rd(bar0.base + 0x48));",
    ind + "}",
]
lines[idx:idx] = blk
io.open(p, "w", encoding="utf-8").write("\n".join(lines))
print("tail moved to apply-169")