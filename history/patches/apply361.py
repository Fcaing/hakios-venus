import re, sys

P = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
src = open(P).read()
orig = src

# 1. declaration
anchor = "static uint32_t pcie_rddm;"
assert src.count(anchor) == 1, ("decl anchor", src.count(anchor))
src = src.replace(anchor, anchor + "\nstatic uint32_t pcie_noearlystate;	/* apply-361: write nothing to MHICTRL before ee 2 */")

# 2. parse, early in hakios_pcie_init
anchor2 = '\tPE_parse_boot_argn("pcie_only", &pcie_only, sizeof(pcie_only));'
assert src.count(anchor2) == 1, ("parse anchor", src.count(anchor2))
src = src.replace(anchor2, '\tPE_parse_boot_argn("pcie_noearlystate", &pcie_noearlystate, sizeof(pcie_noearlystate));\n' + anchor2)

# 3a. the ctrl-based state write (one place)
pat_a = re.compile(r"(?m)^(\t*)wr\(bar0\.base \+ 0x38, \(ctrl & ~0xff00u\) \| \(2u << 8\)\);$")
n_a = len(pat_a.findall(src))
assert n_a == 1, ("a", n_a)
src = pat_a.sub(lambda m: (m.group(1) + "if (pcie_noearlystate == 0 || rd(bar0.base + 0x128) == 2u) {\t/* apply-361 */\n"
                           + m.group(1) + "\twr(bar0.base + 0x38, (ctrl & ~0xff00u) | (2u << 8));\n"
                           + m.group(1) + "}"), src)

# 3b. the rd()-based state write (two places: 2581 and 3003)
pat_b = re.compile(r"(?m)^(\t*)wr\(bar0\.base \+ 0x38, \(rd\(bar0\.base \+ 0x38\) & ~0xff00u\) \| \(2u << 8\)\);$")
n_b = len(pat_b.findall(src))
assert n_b == 2, ("b", n_b)
src = pat_b.sub(lambda m: (m.group(1) + "if (pcie_noearlystate == 0 || rd(bar0.base + 0x128) == 2u) {\t/* apply-361 */\n"
                           + m.group(1) + "\twr(bar0.base + 0x38, (rd(bar0.base + 0x38) & ~0xff00u) | (2u << 8));\n"
                           + m.group(1) + "}"), src)

open(P, "w").write(src)
print("apply-361 ok: decl 1, parse 1, guards", 1 + n_b)
