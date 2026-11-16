p='/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.input.c'
s=open(p).read()
old='\thakios_pcie_dma_init();'
print("count:", s.count(old))
if s.count(old)==1:
    s = s.replace(old, '\t/* apply-155: dma_init left out, p142/p143 panic with pcie=1 and nothing else */\n\t/* hakios_pcie_dma_init(); */')
    open(p,'w').write(s)
    print("patched")