p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(p, encoding="utf-8").read()
n0 = len(s)

def rep(old, new, tag):
    global s
    if s.count(old) != 1:
        raise SystemExit("anchor %s count=%d" % (tag, s.count(old)))
    s = s.replace(old, new, 1)

rep("\t\t\t\t\tprintf(\"pcie: 5:   21: apply-232: bhi gets addr 0x%llx size 0x%llx (fw 0x%llx)\\n\",\n"
    "\t\t\t\t\t    (unsigned long long)bhi_addr, (unsigned long long)bhi_size,\n"
    "\t\t\t\t\t    (unsigned long long)pcie_fw_size);",
    "\t\t\t\t\tprintf(\"pcie: 5:   21: apply-232: bhi gets addr 0x%llx size 0x%llx (fw 0x%llx)\\n\",\n"
    "\t\t\t\t\t    (unsigned long long)bhi_addr, (unsigned long long)bhi_size,\n"
    "\t\t\t\t\t    (unsigned long long)pcie_fw_size);\n"
    "\t\t\t\t\t/* apply-233: everything star reads before it rings the doorbell */\n"
    "\t\t\t\t\tprintf(\"pcie: 5:   21: mhi 00 0x%08x, ver 08 0x%08x, ctrl 10 0x%08x, cfg 18 0x%08x, db 20 0x%08x\\n\",\n"
    "\t\t\t\t\t    rd(bar0.base + 0x00), rd(bar0.base + 0x08), rd(bar0.base + 0x10),\n"
    "\t\t\t\t\t    rd(bar0.base + 0x18), rd(bar0.base + 0x20));\n"
    "\t\t\t\t\tprintf(\"pcie: 5:   21: mhi 38 0x%08x, 48 0x%08x, 4c 0x%08x; bhi 28 0x%08x bhie 2c 0x%08x dbg 30 0x%08x\\n\",\n"
    "\t\t\t\t\t    rd(bar0.base + 0x38), rd(bar0.base + 0x48), rd(bar0.base + 0x4c),\n"
    "\t\t\t\t\t    rd(bar0.base + 0x28), rd(bar0.base + 0x2c), rd(bar0.base + 0x30));\n"
    "\t\t\t\t\tprintf(\"pcie: 5:   21: bhi win: serial 0x%08x numseg 0x%08x msmhwid 0x%08x, ee 0x%08x status 0x%08x err 0x%08x\\n\",\n"
    "\t\t\t\t\t    rd(bar0.base + 0x140), rd(bar0.base + 0x148), rd(bar0.base + 0x14c),\n"
    "\t\t\t\t\t    rd(bar0.base + 0x128), rd(bar0.base + 0x12c), rd(bar0.base + 0x130));",
    "regs")

rep("\t\t\t\t\tuint32_t db;\n"
    "\n"
    "\t\t\t\t\tseed = seed * 1103515245u + 12345u;\n"
    "\t\t\t\t\tdb = (seed >> 2) & 0x3fffffffu;\n"
    "\t\t\t\t\tif (db == 0) {\n"
    "\t\t\t\t\t\tdb = 1;\n"
    "\t\t\t\t\t}",
    "\t\t\t\t\tuint32_t db, want_db = 1;\n"
    "\n"
    "\t\t\t\t\t/* apply-233: star rings this doorbell with 1, always */\n"
    "\t\t\t\t\tPE_parse_boot_argn(\"pcie_db\", &want_db, sizeof(want_db));\n"
    "\t\t\t\t\tseed = seed * 1103515245u + 12345u;\n"
    "\t\t\t\t\tdb = want_db != 0 ? want_db : ((seed >> 2) & 0x3fffffffu);\n"
    "\t\t\t\t\tif (db == 0) {\n"
    "\t\t\t\t\t\tdb = 1;\n"
    "\t\t\t\t\t}",
    "db1")

open(p, "w", encoding="utf-8").write(s)
print("ok %d -> %d" % (n0, len(s)))