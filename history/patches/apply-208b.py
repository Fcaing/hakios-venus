import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
old = "#define VOTE_0_MASK                    0x004c0c00u"
new = ("#define VOTE_0_MASK                    0x004c1c00u"
       " /* apply-208: bit 12 is gcc_aggre_noc_pcie_0_axi_clk (gcc-lahaina.c:1812);\n"
       "\t\t\t\t\t\t\t\t\t  * without it the endpoint's AXI path into DDR is halted */")
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("ok apply-208b")