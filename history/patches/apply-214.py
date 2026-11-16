import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

marker_start = "\t\t\t\t/*\n\t\t\t\t * apply-199: p196 showed both inbound iATU windows are empty"
marker_end = "\t\t\t\tprintf(\"pcie: 5:   21: bhi before: soc 0x%08x ee 0x%08x mhi 0x%08x status 0x%08x err 0x%08x\\n\","
assert s.count(marker_start) == 1, s.count(marker_start)
assert s.count(marker_end) == 1, s.count(marker_end)

s = s.replace(marker_start,
    "\t\t\t\t/* apply-214: the inbound iATU window was eating the SMMU test. p209: FAR\n"
    "\t\t\t\t * was 0x19252c000, the iATU's own translation of 0xa0004000, so the\n"
    "\t\t\t\t * endpoint's address was turned into a physical address BEFORE the\n"
    "\t\t\t\t * SMMU saw it, and the SMMU then faulted on that physical address. */\n"
    "\t\t\t\t#if 0\n" + marker_start, 1)
s = s.replace(marker_end, "\t\t\t\t#endif\n" + marker_end, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("ok apply-214")