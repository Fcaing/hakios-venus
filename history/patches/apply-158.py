p='/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c'
s=open(p).read()
old='''	PE_parse_boot_argn("pcie_return", &pcie_return, sizeof(pcie_return));
'''
new='''	PE_parse_boot_argn("pcie_return", &pcie_return, sizeof(pcie_return));
	{
		uint32_t pcie_probe = 0;
		if (PE_parse_boot_argn("pcie_probe", &pcie_probe, sizeof(pcie_probe)) && pcie_probe != 0) {
			return;         /* apply-158: stop right after the boot args */
		}
	}
'''
print("count:", s.count(old))
if s.count(old)==1:
    s = s.replace(old, new)
    open(p,'w').write(s)
    print("patched")