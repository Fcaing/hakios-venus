import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old = '''	n = fsize < PCIE_DMA_SIZE ? (uint32_t)fsize : PCIE_DMA_SIZE;
	memcpy((void *)pcie_dma, fw, n);
'''
new = '''	n = fsize < PCIE_DMA_SIZE ? (uint32_t)fsize : PCIE_DMA_SIZE;
	memcpy((void *)pcie_dma, fw, n);
	/*
	 * apply-221: the corrupt image probe.  Feeding the PBL something that is
	 * not an ELF tells us whether it parses the image at all: a different
	 * ERRCODE means it does, and the same SUCCESS followed by no jump means
	 * it never gets that far.  Only the BHI page is spoiled; the BHIE image
	 * at pcie_dma_extra keeps the real firmware.
	 */
	{
		uint32_t corrupt = 0;

		if (PE_parse_boot_argn("pcie_corrupt", &corrupt, sizeof(corrupt)) && corrupt != 0) {
			uint32_t k;

			for (k = 0; k < 64u && k < n; k++) {
				((uint8_t *)pcie_dma)[k] = 0xAA;
			}
			printf("pcie: stage: the first %u bytes of the image were overwritten with 0xaa\n",
			       k);
		}
	}
'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("ok apply-221 (written, not built yet)")