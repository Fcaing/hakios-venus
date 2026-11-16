import io, os

# ---- 1. pcie.c: kmem_alloc_contig at the head of the boot path ----
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(p).read()
old = '\t} else {\n\t\tprintf("pcie: no pcie_dma_pa= on the command line\\n");\n\t}\n}\n'
new = '''\t} else {
\t\t/*
\t\t * apply-146: ask the kernel for it here instead, exactly as lemonade_wifi.c
\t\t * does on the star (the same SM8350, the same QCA6490), at the head of the
\t\t * boot path where nothing has fragmented the map yet.  p108-p122 asked for
\t\t * it in place and hung, but every one of those runs carried the 7.5 MB root
\t\t * that cannot reach the window server (HANDOVER-2026-11-08.md).
\t\t */
\t\tvm_offset_t buffer = 0;
\t\tprintf("pcie: no pcie_dma_pa= from the loader: asking here, star style\\n");
\t\tkr = kmem_alloc_contig(kernel_map, &buffer, PAGE_SIZE, 0, 0, 0,
\t\t    KMA_KOBJECT | KMA_ZERO | KMA_DATA, VM_KERN_MEMORY_IOKIT);
\t\tprintf("pcie: kmem_alloc_contig(star style) -> kr %d, va 0x%llx\\n",
\t\t       kr, (unsigned long long)buffer);
\t\tif (kr == KERN_SUCCESS && buffer != 0) {
\t\t\tpcie_dma_pa = kvtophys(buffer);
\t\t\tpcie_dma = ml_io_map(pcie_dma_pa, PAGE_SIZE);
\t\t\tprintf("pcie: ... pa 0x%llx, mapped at 0x%llx\\n",
\t\t\t       (unsigned long long)pcie_dma_pa, (unsigned long long)pcie_dma);
\t\t}
\t}
}
'''
if s.count(old) != 1:
    raise SystemExit("pcie.c: pattern count %d" % s.count(old))
s = s.replace(old, new)
open(p, "w").write(s)
print("pcie.c patched")

# ---- 2. input.c: put the call back ----
p2 = "/root/hakios/drivers/input/hakios.input.c"
s2 = open(p2).read()
old2 = '\t/* fix140: out of the boot path */\n\thakios_ufs_init();\n'
new2 = '\t/* fix140: out of the boot path */ /* apply-146: back in, at the head */\n\thakios_pcie_dma_init();\n\thakios_ufs_init();\n'
if s2.count(old2) != 1:
    raise SystemExit("input.c: pattern count %d" % s2.count(old2))
s2 = s2.replace(old2, new2)
open(p2, "w").write(s2)
print("input.c patched")

# ---- 3. does input.c declare it? ----
for i, line in enumerate(open(p2).read().split("\n"), 1):
    if "hakios_pcie_dma_init" in line:
        print("input.c:%d: %s" % (i, line.strip()))