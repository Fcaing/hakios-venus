import io

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old = """		kr = kmem_alloc_contig(kernel_map, &buffer, PCIE_DMA_SIZE, 0, 0xfffff, 0,
		    KMA_KOBJECT | KMA_ZERO | KMA_DATA, VM_KERN_MEMORY_IOKIT);"""
new = """		kr = kmem_alloc_contig(kernel_map, &buffer, PCIE_DMA_SIZE, 0, 0xfffff, 0,
		    KMA_KOBJECT | KMA_ZERO | KMA_DATA | KMA_LOMEM, VM_KERN_MEMORY_IOKIT);"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("patched")