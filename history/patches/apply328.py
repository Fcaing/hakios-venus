import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
if "pcie_bw_db" not in s:
    a = "static uint32_t bw_seq, bw_rp0, bw_rp1, bw_ok;	/* apply-327 */"
    assert s.count(a) == 1
    s = s.replace(a, a + "\nstatic uint32_t pcie_bw_db = 1, pcie_bw_rp = 1;	/* apply-328: split the bw ack steps */")
lines = s.split("\n")
out = []
did_db = did_rp = False
for l in lines:
    st = l.strip()
    if st.startswith("wr(bar0.base + 0x6f0u,"):
        ind = l[:len(l) - len(l.lstrip())]
        out.append(ind + "if (pcie_bw_db != 0) {")
        out.append(l)
        out.append(ind + "}")
        did_db = True
        continue
    if st.startswith("wr(pcie_dma_extra + 0x2000 + 2 * 0x2c + 0x1c, eb26") or st.startswith("wr(bar0.base + 0x700u + 2u * 8u, eb26"):
        ind = l[:len(l) - len(l.lstrip())]
        out.append(ind + "if (pcie_bw_rp != 0) {")
        out.append(l)
        out.append(ind + "}")
        did_rp = True
        continue
    out.append(l)
s = "\n".join(out)
assert did_db and did_rp, (did_db, did_rp)
# parse the two boot args next to the apply-314 parse
needle = 'PE_parse_boot_argn("pcie_mhi_state_val"'
i = s.index(needle)
j = s.index("}", s.index(";", i)) + 1
add = ('\n\t\t\t\t\t\t{\n\t\t\t\t\t\t\tuint32_t d33 = pcie_bw_db;\n'
       '\t\t\t\t\t\t\tif (PE_parse_boot_argn("pcie_bw_db", &d33, sizeof(d33))) { pcie_bw_db = d33; }\n'
       '\t\t\t\t\t\t\td33 = pcie_bw_rp;\n'
       '\t\t\t\t\t\t\tif (PE_parse_boot_argn("pcie_bw_rp", &d33, sizeof(d33))) { pcie_bw_rp = d33; }\n'
       '\t\t\t\t\t\t}')
s = s[:j] + add + s[j:]
io.open(p, "w", encoding="utf-8").write(s)
print("apply-328 split ok")