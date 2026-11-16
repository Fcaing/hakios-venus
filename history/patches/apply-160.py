p='/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c'
s=open(p).read()
old='''	return;         /* apply-159: the whole body left out, p149 hung with pcie_probe=1 */
'''
print("count:", s.count(old))
if s.count(old)==1:
    s = s.replace(old, '')
    open(p,'w').write(s)
    print("reverted apply-159")