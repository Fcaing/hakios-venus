import io
p="/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s=io.open(p,encoding="utf-8").read()
old="\t\t\t\t\t\twr(bar0.base + 0x38, (m0old & ~0xff00u) | (pcie_mhi_state_val << 8));\n"
assert s.count(old)==1
new=("\t\t\t\t\t\tif (pcie_m0_delay != 0) {\n"
     "\t\t\t\t\t\t\tsleep_ms(pcie_m0_delay);\n"
     "\t\t\t\t\t\t}\n"
     "\t\t\t\t\t\twr(bar0.base + 0x38, (m0old & ~0xff00u) | (pcie_mhi_state_val << 8));\n")
s=s.replace(old,new,1)
decl="static uint32_t pcie_rp_fix = 1;"
assert s.count(decl)==1
s=s.replace(decl, decl+"\t/* apply-339: wait this long before asking for a power state */\nstatic uint32_t pcie_m0_delay;",1)
anchor='\t\t\t\t\t\t\twant2 = 0;\n\t\t\t\t\t\t\tif (PE_parse_boot_argn("pcie_rp_fix", &want2, sizeof(want2))) {\n'
assert s.count(anchor)==1
s=s.replace(anchor, anchor+'\t\t\t\t\t\t\twant2 = 0;\n\t\t\t\t\t\t\tif (PE_parse_boot_argn("pcie_m0_delay", &want2, sizeof(want2))) {\n\t\t\t\t\t\t\t\tpcie_m0_delay = want2;\n\t\t\t\t\t\t\t}\n',1)
io.open(p,"w",encoding="utf-8").write(s)
print("apply-339 ok")