import io, re
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
orig = s

# 1. new boot argument
a1 = "static uint32_t pcie_headonly;\t/* apply-245: map only page 0 of the staging window */\n"
assert s.count(a1) == 1
s = s.replace(a1, a1 + "static uint32_t pcie_headonly_pages;\t/* apply-246: how many staging pages stay mapped */\nstatic uint32_t pcie_msi_test;\t\t/* apply-246: point the endpoint's msi at our own page */\n")

# 2. parse it
a2 = """\tif (PE_parse_boot_argn("pcie_headonly", &headonly, sizeof(headonly))) {
\t\tpcie_headonly = headonly;
\t}
"""
assert s.count(a2) == 1
s = s.replace(a2, a2 + """\t{
\t\tuint32_t pages = 0;

\t\tif (PE_parse_boot_argn("pcie_headonly_pages", &pages, sizeof(pages))) {
\t\t\tpcie_headonly_pages = pages;
\t\t}
\t\tif (PE_parse_boot_argn("pcie_msi_test", &pages, sizeof(pages))) {
\t\t\tpcie_msi_test = pages;
\t\t}
\t}
""")

# 3. map N pages instead of one
a3 = """\t\tif (pcie_headonly != 0 && page != 0) {
\t\t\tcontinue;
\t\t}
"""
assert s.count(a3) == 1
s = s.replace(a3, """\t\tif (pcie_headonly != 0 &&
\t\t    page >= (pcie_headonly_pages != 0 ? pcie_headonly_pages : 1u)) {
\t\t\tcontinue;
\t\t}
""")

# 4. report how many
a4 = """\tif (pcie_headonly != 0) {
\t\tprintf("pcie: smmu: apply-245 headonly: only page 0 of the staging window is mapped\\n");
\t}
"""
assert s.count(a4) == 1
s = s.replace(a4, """\tif (pcie_headonly != 0) {
\t\tprintf("pcie: smmu: apply-246 headonly: %u of %u pages mapped, %u bytes reachable\\n",
\t\t    pcie_headonly_pages != 0 ? pcie_headonly_pages : 1u, PCIE_DMA_SIZE / 4096,
\t\t    (pcie_headonly_pages != 0 ? pcie_headonly_pages : 1u) * 4096);
\t}
""")
io.open(p, "w", encoding="utf-8").write(s)
print("apply-246 part 1 done:", len(orig), "->", len(s))