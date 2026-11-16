p='/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c'
s=open(p).read()
old='''		b->base = ml_io_map_unmappable(b->phys, b->size, VM_WIMG_IO);
'''
new='''		b->base = ml_io_map(b->phys, b->size);   /* apply-161: back to io_submap; unmappable allocates from kernel_map and hangs here */
'''
print("count:", s.count(old))
if s.count(old)==1:
    s = s.replace(old, new)
    open(p,'w').write(s)
    print("patched")