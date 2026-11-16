import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
def sub1(old, new):
    global s
    assert s.count(old) == 1, ("count", s.count(old), old[:60])
    s = s.replace(old, new, 1)

sub1("""#define PCIE_SMMU_VEC_IOVA  0xa0084000ull
""", """#define PCIE_SMMU_VEC_IOVA  0xa0084000ull
/* apply-218: the 8 MiB region star keeps at WIFI_MHI_IOVA (0xa0200000), where
 * the whole firmware image lives and the BHIE vectors point.  SBL reads the
 * image from here after the BHI transfer hands it the first 512 KiB. */
#define PCIE_EXTRA_IOVA     0xa0200000ull
#define PCIE_EXTRA_SIZE     (8u * 1024 * 1024)
#define PCIE_EXTRA_DATA_OFF 0x20000u
""")

sub1("""static vm_offset_t smmu_mmio, smmu_cb, smmu_tables;
""", """static vm_offset_t smmu_mmio, smmu_cb, smmu_tables;
static vm_offset_t pcie_dma_extra;      /* apply-218: the 8 MiB image region */
""")

sub1("""	uint64_t *l1, *l2, *l3, root, physical;
	unsigned page;
""", """	uint64_t *l1, *l2, *l3, *l3x[4], root, physical;
	unsigned page;
""")

sub1("""	if (kmem_alloc(kernel_map, &smmu_tables, 3 * PAGE_SIZE,
""", """	if (kmem_alloc(kernel_map, &smmu_tables, 7 * PAGE_SIZE,
""")

sub1("""	l1[(PCIE_SMMU_IOVA >> 30) & 511] = kvtophys(smmu_tables + PAGE_SIZE) | 3;
	l2[(PCIE_SMMU_IOVA >> 21) & 511] = kvtophys(smmu_tables + 2 * PAGE_SIZE) | 3;
""", """	l1[(PCIE_SMMU_IOVA >> 30) & 511] = kvtophys(smmu_tables + PAGE_SIZE) | 3;
	l2[(PCIE_SMMU_IOVA >> 21) & 511] = kvtophys(smmu_tables + 2 * PAGE_SIZE) | 3;
	/*
	 * apply-218: four more L3 tables cover the 8 MiB image region at
	 * 0xa0200000.  SBL loads the rest of the firmware from here, so the
	 * context bank has to translate it before the BHI doorbell rings.
	 */
	if (pcie_dma_extra != 0) {
		for (i = 0; i < 4; i++) {
			l3x[i] = (uint64_t *)(smmu_tables + (3 + i) * PAGE_SIZE);
			l2[((PCIE_EXTRA_IOVA >> 21) & 511) + i] =
			    kvtophys(smmu_tables + (3 + i) * PAGE_SIZE) | 3;
		}
		for (page = 0; page < PCIE_EXTRA_SIZE / 4096; page++) {
			physical = kvtophys(pcie_dma_extra + page * 4096);
			if (physical == 0) {
				printf("pcie: smmu: image page %u has no physical address\\n", page);
				return false;
			}
			l3x[page / 512][page % 512] =
			    physical | 3ull | (1ull << 6) | (2ull << 8) | (1ull << 10) |
			    (1ull << 11) | (1ull << 53) | (1ull << 54);
		}
		printf("pcie: smmu: image region 0x%llx -> 0x%llx, %u pages\\n",
		       (unsigned long long)PCIE_EXTRA_IOVA,
		       (unsigned long long)kvtophys(pcie_dma_extra),
		       PCIE_EXTRA_SIZE / 4096);
	}
""")

sub1("""	pcie_table_flush(smmu_tables, 3 * PAGE_SIZE);
""", """	pcie_table_flush(smmu_tables, 7 * PAGE_SIZE);
""")

io.open(p, "w", encoding="utf-8").write(s)
print("ok apply-218 part 1")