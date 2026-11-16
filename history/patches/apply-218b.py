import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
def sub1(old, new):
    global s
    assert s.count(old) == 1, ("count", s.count(old), old[:80])
    s = s.replace(old, new, 1)

# dma_init: allocate the 8 MiB image region right after the vector page.
sub1("""			} else {
				printf("pcie: dma init: vector page -> kr %d, va 0x%llx\\n",
				       kr, (unsigned long long)vbuf);
			}
		}
""", """			} else {
				printf("pcie: dma init: vector page -> kr %d, va 0x%llx\\n",
				       kr, (unsigned long long)vbuf);
			}
		}
		/*
		 * apply-218: the 8 MiB region the BHIE vectors point at.  The whole
		 * amss.bin (5 MiB) goes here; star keeps the same layout at
		 * WIFI_MHI_IOVA.  Not contiguous: the SMMU maps it page by page.
		 */
		if (pcie_dma_pa != 0 && pcie_dma_extra == 0) {
			vm_offset_t ebuf = 0;

			kr = kmem_alloc(kernel_map, &ebuf, PCIE_EXTRA_SIZE,
			    KMA_KOBJECT | KMA_ZERO | KMA_DATA, VM_KERN_MEMORY_IOKIT);
			if (kr == KERN_SUCCESS && ebuf != 0) {
				pcie_dma_extra = ebuf;
				printf("pcie: dma init: image region at 0x%llx, 0x%x bytes\\n",
				       (unsigned long long)pcie_dma_extra, PCIE_EXTRA_SIZE);
			} else {
				printf("pcie: dma init: image region -> kr %d, va 0x%llx\\n",
				       kr, (unsigned long long)ebuf);
			}
		}
""")

# stage: copy the whole image into the extra region as well.
sub1("""	pcie_dma_staged = 1;
	printf("pcie: stage: copied %u bytes of 0x%llx from amss.bin to 0x%llx (pa 0x%llx), first word 0x%08x\\n",
""", """	if (pcie_dma_extra != 0) {
		vm_offset_t dst = pcie_dma_extra + PCIE_EXTRA_DATA_OFF;
		uint32_t room = PCIE_EXTRA_SIZE - PCIE_EXTRA_DATA_OFF;
		uint32_t en = fsize < room ? (uint32_t)fsize : room;

		memcpy((void *)dst, fw, en);
		for (i = 0; i < en; i += 64) {
			__asm__ volatile ("dc civac, %0" : : "r" (dst + i) : "memory");
		}
		__asm__ volatile ("dsb sy" : : : "memory");
		printf("pcie: stage: image 0x%x bytes at 0x%llx (iova 0x%llx), first word 0x%08x\\n",
		       en, (unsigned long long)dst,
		       (unsigned long long)(PCIE_EXTRA_IOVA + PCIE_EXTRA_DATA_OFF), rd(dst));
	}
	pcie_dma_staged = 1;
	printf("pcie: stage: copied %u bytes of 0x%llx from amss.bin to 0x%llx (pa 0x%llx), first word 0x%08x\\n",
""")

io.open(p, "w", encoding="utf-8").write(s)
print("ok apply-218 part 2")