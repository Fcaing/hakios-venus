p='/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c'
s=open(p).read()
old1='''			pcie_flush("power");
'''
new1='''			/* apply-162: pcie_flush left out, p154 hung at step 1 */
'''
old2='''		pcie_flush("step");
'''
new2='''		/* pcie_flush("step"); */
'''
old3='''			pcie_flush("link");
'''
new3='''			/* pcie_flush("link"); */
'''
n=0
for o,nw in [(old1,new1),(old2,new2),(old3,new3)]:
    c=s.count(o)
    print(repr(o[:20]), "count:", c)
    if c>=1:
        s=s.replace(o,nw)
        n+=1
open(p,'w').write(s)
print("patched groups:", n)