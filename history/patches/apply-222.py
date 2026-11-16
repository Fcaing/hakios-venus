import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

anchor = "\t\t\t\t\twr(bar0.base + 0x118, db);"
assert s.count(anchor) == 1, s.count(anchor)

block = r'''					/*
					 * apply-222: vendor builds the BHIE vector table right after the
					 * BHI transfer and before it waits for READY (mhi_boot.c:586-733).
					 * Building it after the wait left the table empty for the whole
					 * fifteen seconds the probe sits looking at MHISTATUS.
					 */
					if (smmu_state == 1 && pcie_dma_extra != 0 &&
					    pcie_dma_vec_pa != 0 && pcie_fw_size != 0) {
						vm_offset_t pv = ml_io_map_unmappable(
							(vm_offset_t)pcie_dma_vec_pa, PAGE_SIZE, VM_WIMG_IO);
						uint64_t voff = 0;
						uint32_t nvec = 0, k;

						if (pv != 0) {
							while (voff < pcie_fw_size && nvec < 64) {
								uint64_t left = pcie_fw_size - voff;
								uint32_t chunk = left > PCIE_DMA_SIZE ?
									PCIE_DMA_SIZE : (uint32_t)left;
								uint64_t addr =
									PCIE_EXTRA_IOVA + PCIE_EXTRA_DATA_OFF + voff;

								wr(pv + nvec * 16 + 0, (uint32_t)addr);
								wr(pv + nvec * 16 + 4, (uint32_t)(addr >> 32));
								wr(pv + nvec * 16 + 8, chunk);
								wr(pv + nvec * 16 + 12, 0);
								nvec++;
								voff += chunk;
							}
							for (k = 0; k < nvec * 16; k += 64) {
								__asm__ __volatile__("dc civac, %0"
									:: "r"(pv + (vm_offset_t)k) : "memory");
							}
							__asm__ __volatile__("dsb sy" ::: "memory");
							wr(bar0.base + 0x224 + 0x30,
								(uint32_t)(PCIE_SMMU_VEC_IOVA >> 32));
							wr(bar0.base + 0x224 + 0x2c,
								(uint32_t)PCIE_SMMU_VEC_IOVA);
							wr(bar0.base + 0x224 + 0x34, nvec * 16);
							printf("pcie: 5:   21: apply-222: %u vectors "
								"ready before the bhi doorbell\n", nvec);
							pcie_note("vec %u before bhi; ", nvec);
						}
					}
'''
s = s.replace(anchor, block + anchor, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("ok apply-222")
# verify
s2 = io.open(p, encoding="utf-8").read()
print("marker count:", s2.count("apply-222"))