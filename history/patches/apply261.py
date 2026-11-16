import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

# 1. file-scope scratch for the ring watch
anchor1 = "static uint32_t pcie_mhi_init = 1;\t/* apply-251: program the mhi mmio and ask for m0 */"
assert s.count(anchor1) == 1
s = s.replace(anchor1, anchor1 + """
/* apply-261: the ring watch runs in the middle of the run, but the log ring
 * is a fifo and the ios boot that follows overwrites it.  Keep the answer in
 * these and print it at the very end, where it is the newest line. */
static uint32_t pcie_ring_changes;
static uint32_t pcie_ring_er_wp;
static uint32_t pcie_ring_ch_wp;
static uint32_t pcie_ring_first;
static uint32_t pcie_ring_ee;""")

# 2. record inside the watch loop
anchor2 = """\t\t\t\t\t\t\tprev_er = er_wp;
\t\t\t\t\t\t\tprev_ch = ch_wp;"""
assert s.count(anchor2) == 1
s = s.replace(anchor2, """\t\t\t\t\t\t\tif (er_wp != prev_er || ch_wp != prev_ch)
\t\t\t\t\t\t\t\tpcie_ring_changes++;
\t\t\t\t\t\t\tpcie_ring_er_wp = er_wp;
\t\t\t\t\t\t\tpcie_ring_ch_wp = ch_wp;
\t\t\t\t\t\t\tpcie_ring_first = first;
\t\t\t\t\t\t\tpcie_ring_ee = ee2;
\t\t\t\t\t\t\tprev_er = er_wp;
\t\t\t\t\t\t\tprev_ch = ch_wp;""")

# 3. print it as one of the last lines
anchor3 = """\t\tprintf("pcie: 5:   21: bhi after: status 0x%08x (top %u, ee %u) mhi 0x%08x err 0x%08x\\n","""
assert s.count(anchor3) == 1
s = s.replace(anchor3, """\t\tprintf("pcie: 5:   21: apply-261 ring watch: %u changes, er0 wp 0x%08x ch20 wp 0x%08x er0[0] 0x%08x ee 0x%08x\\n",
\t\t    pcie_ring_changes, pcie_ring_er_wp, pcie_ring_ch_wp, pcie_ring_first, pcie_ring_ee);
""" + anchor3)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-261 inserted", len(s))