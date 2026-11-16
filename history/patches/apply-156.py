p='/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c'
s=open(p).read()
old='\tpcie_flush("start");\n'
print("count:", s.count(old))
if s.count(old)==1:
    s = s.replace(old, '\t/* apply-156: pcie_flush left out, p144/p145 panic with pcie=1 and step 0 */\n\t/* pcie_flush("start"); */\n')
    open(p,'w').write(s)
    print("patched")