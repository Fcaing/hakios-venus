import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
if "pcie_gen" not in s:
    a = "static uint32_t pcie_bw_db = 1, pcie_bw_rp = 1;\t/* apply-328: split the bw ack steps */"
    assert s.count(a) == 1
    s = s.replace(a, a + "\nstatic uint32_t pcie_gen = 1;\t/* apply-330: target link speed (1=gen1, 2=gen2) */")
lines = s.split("\n")
out = []
done = False
for l in lines:
    st = l.strip()
    if (not done) and ("GEN1" in l or "gen1" in l) and st.startswith("wr(") and "0xa0" in l:
        ind = l[:len(l) - len(l.lstrip())]
        out.append(ind + "printf(\"pcie: 4:   apply-330 gen target %u, dbi 0xa0 0x%08x\\n\", pcie_gen, rd(bar0.base + 0xa0));")
        done = True
    out.append(l)
s = "\n".join(out)
print("gen hook:", done)
io.open(p, "w", encoding="utf-8").write(s)