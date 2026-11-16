p='/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c'
s=open(p).read()
old='''	printf("pcie: the root complex of this phone, up to step %u%s\\n", pcie_step_last,
	       pcie_only ? " (one step)" : "");
'''
print("count:", s.count(old))
if s.count(old)==1:
    s = s.replace(old, '''	/* apply-157: the first printf left out too, p146 hung with pcie=1 and step 0 */
	if (0) {
	printf("pcie: the root complex of this phone, up to step %u%s\\n", pcie_step_last,
	       pcie_only ? " (one step)" : "");
	}
''')
    open(p,'w').write(s)
    print("patched")