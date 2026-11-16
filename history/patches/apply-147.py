p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(p).read()
start = s.index("void\nhakios_pcie_dma_init(void)\n{")
end = s.index("\nvoid\nhakios_pcie_init(void)", start)
old = s[start:end]
print("=== OLD (%d bytes) ===" % len(old))
print(old)
new = '''void
hakios_pcie_dma_init(void)
{
	uint32_t wants = 0;
	kern_return_t kr;

	if (pcie_dma != 0 || !PE_parse_boot_argn("pcie", &wants, sizeof(wants)) || wants == 0) {
		return;
	}
	/*
	 * apply-147: take the page here, map it at step 5.  ml_io_map() is not usable
	 * this early -- it enters io_submap, which is not set up yet, and p130 (this
	 * function calling ml_io_map on the loader's page) panicked instead of logging.
	 * kmem_alloc_contig() is fine this early: hakios.ufshc.c:1273 makes the same
	 * call a few lines further down the boot path.
	 */
	if (PE_parse_boot_argn("pcie_dma_pa", &pcie_dma_pa, sizeof(pcie_dma_pa)) && pcie_dma_pa != 0) {
		printf("pcie: dma init: the loader's page 0x%llx, mapped at step 5\\n",
		       (unsigned long long)pcie_dma_pa);
		return;
	}
	{
		vm_offset_t buffer = 0;
		printf("pcie: dma init: asking for a page (mask PAGE_MASK, as ufshc does)\\n");
		kr = kmem_alloc_contig(kernel_map, &buffer, PAGE_SIZE, PAGE_MASK, 0, 0,
		    KMA_KOBJECT | KMA_ZERO | KMA_DATA, VM_KERN_MEMORY_IOKIT);
		printf("pcie: dma init: kmem_alloc_contig -> kr %d, va 0x%llx\\n",
		       kr, (unsigned long long)buffer);
		if (kr == KERN_SUCCESS && buffer != 0) {
			pcie_dma_pa = kvtophys(buffer);
			printf("pcie: dma init: pa 0x%llx, mapped at step 5\\n",
			       (unsigned long long)pcie_dma_pa);
		}
	}
}
'''
s = s[:start] + new + s[end:]
open(p, "w").write(s)
print("=== patched ===")