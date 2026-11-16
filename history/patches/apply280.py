import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
lines = io.open(p, encoding="utf-8").read().split("\n")

if not any("pcie_mhi_m0late;" in l for l in lines):
    for i, l in enumerate(lines):
        if l.strip() == "static uint32_t pcie_mhi_nom0;":
            lines.insert(i + 1, "static uint32_t pcie_mhi_m0late;")
            break

for i, l in enumerate(lines):
    if l.strip() == "if (pcie_mhi_nom0 == 0) {":
        lines[i] = l.replace("if (pcie_mhi_nom0 == 0) {", "if (pcie_mhi_nom0 == 0 && pcie_mhi_m0late == 0) {")
        break

# find bhie printf line index
bi = None
for i, l in enumerate(lines):
    if "bhie after %u ms:" in l:
        bi = i
        break
assert bi is not None
indent = lines[bi][:len(lines[bi]) - len(lines[bi].lstrip("\t"))]

if not any("apply-280 m0 after bhie" in l for l in lines):
    block = [
        indent + "if (pcie_mhi_m0late != 0) {",
        indent + "\twr(bar0.base + 0x38, (rd(bar0.base + 0x38) & ~0xff00u) | (2u << 8));",
        indent + "\tsleep_ms(5);",
        indent + "\tprintf(\"pcie: 5:   21: apply-280 m0 after bhie: mh 0x%08x ee 0x%08x ctrl 0x%08x\\n\",",
        indent + "\t    rd(bar0.base + 0x48), rd(bar0.base + 0x128), rd(bar0.base + 0x38));",
        indent + "}",
    ]
    lines[bi:bi] = block

# parse boot arg just before the apply-264 printf
if not any('PE_parse_boot_argn("pcie_mhi_m0late"' in l for l in lines):
    for i, l in enumerate(lines):
        if "apply-264 before init:" in l:
            ind = l[:len(l) - len(l.lstrip("\t"))]
            block = [
                ind + "{",
                ind + "\tuint32_t late = 0;",
                "",
                ind + "\tPE_parse_boot_argn(\"pcie_mhi_m0late\", &late, sizeof(late));",
                ind + "\tpcie_mhi_m0late = late;",
                ind + "}",
            ]
            lines[i:i] = block
            break

io.open(p, "w", encoding="utf-8").write("\n".join(lines))
print("apply-280 applied")