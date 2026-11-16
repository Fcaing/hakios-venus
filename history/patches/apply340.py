import io
p="/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
lines=io.open(p,encoding="utf-8").read().split("\n")

def block_span(marker, start_hint):
    # find the comment line containing marker
    i=None
    for k,l in enumerate(lines):
        if marker in l:
            i=k; break
    assert i is not None, marker
    # scan back to the comment start "/*"
    s=i
    while "/*" not in lines[s]:
        s-=1
    # now find matching brace: from the line that opens the if(...)
    j=s
    while "{" not in lines[j]:
        j+=1
    depth=0
    k=j
    while True:
        depth += lines[k].count("{") - lines[k].count("}")
        if depth==0:
            break
        k+=1
    return s,k

s1,e1 = block_span("apply-336:", None)
lines = lines[:s1] + ["#if 0\t/* apply-340: the apply-336 probe shifted the device timing */"] + lines[s1:e1+1] + ["#endif"] + lines[e1+1:]
s2,e2 = block_span("apply-337:", None)
lines = lines[:s2] + ["#if 0\t/* apply-340: same for the apply-337 block */"] + lines[s2:e2+1] + ["#endif"] + lines[e2+1:]
io.open(p,"w",encoding="utf-8").write("\n".join(lines))
print("apply-340 disabled both blocks")