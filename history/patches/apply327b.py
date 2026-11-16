import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
if "bw_seq, bw_rp0" not in s:
    a = "static uint32_t pcie_chanlate;"
    assert s.count(a) == 1
    s = s.replace(a, "static uint32_t bw_seq, bw_rp0, bw_rp1, bw_ok;	/* apply-327 */\n" + a)
lines = s.split("\n")
out = []
done = False
for l in lines:
    if (not done) and ("apply-326 bw req after" in l) and l.lstrip().startswith("printf("):
        ind = l[:len(l) - len(l.lstrip())]
        out.append(ind + "bw_ok = 1u; bw_seq = seq; bw_rp0 = eb26; bw_rp1 = rp26;")
        done = True
    out.append(l)
assert done
s = "\n".join(out)
if "apply-327 tail" not in s:
    lines = s.split("\n")
    idx = None
    for i, l in enumerate(lines):
        if "apply-225 final:" in l:
            idx = i
    assert idx is not None
    ind = lines[idx][:len(lines[idx]) - len(lines[idx].lstrip())]
    blk = [
        ind + "__asm__ volatile (\"dc ivac, %0\" : : \"r\" (pcie_dma_extra + 20 * 0x2c + 0x1c) : \"memory\");",
        ind + "__asm__ volatile (\"dsb sy\" : : : \"memory\");",
        ind + "printf(\"pcie: 5:   21: apply-327 tail: bw ok %u seq %u rp0 0x%08x rp1 0x%08x ch20 rp 0x%08x wp 0x%08x ee 0x%08x mh 0x%08x\\n\",",
        ind + "    bw_ok, bw_seq, bw_rp0, bw_rp1,",
        ind + "    *(volatile uint32_t *)(pcie_dma_extra + 20 * 0x2c + 0x1c),",
        ind + "    *(volatile uint32_t *)(pcie_dma_extra + 20 * 0x2c + 0x24),",
        ind + "    rd(bar0.base + 0x128), rd(bar0.base + 0x48));",
        "",
    ]
    lines[idx:idx] = blk
    s = "\n".join(lines)
io.open(p, "w", encoding="utf-8").write(s)
print("patched")