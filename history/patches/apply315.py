import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
anchor = "\t\t\t\t\t/* apply-308: the vendor only writes the channel contexts once"
assert s.count(anchor) == 1
block = """\t\t\t\t\t/* apply-315: the vendor walks m2 -> m0 through mhi_set_mhi_state()
\t\t\t\t\t * when it resumes.  We could reach m2 but the device then stopped
\t\t\t\t\t * servicing the command ring, so try the walk back down the way the
\t\t\t\t\t * vendor does it. */
\t\t\t\t\tif (pcie_mhi_state_val == 4u && pcie_chanstart != 0 && smmu_state == 1) {
\t\t\t\t\t\tuint32_t m5;

\t\t\t\t\t\tm5 = rd(bar0.base + 0x38);
\t\t\t\t\t\twr(bar0.base + 0x38, (m5 & ~0xff00u) | (2u << 8));
\t\t\t\t\t\tsleep_ms(5);
\t\t\t\t\t\tprintf("pcie: 5:   21: apply-315 m2 to m0: mh 0x%08x ee 0x%08x ctrl 0x%08x\\n",
\t\t\t\t\t\t    rd(bar0.base + 0x48), rd(bar0.base + 0x128), rd(bar0.base + 0x38));
\t\t\t\t\t}
"""
s = s.replace(anchor, block + anchor)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-315 written")