import io

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

smmu = r"""
/* apply-176: the SMMU, the way star's lemonade_wifi.c does it (dma_prepare,
 * lemonade_wifi.c:592).  BHI is handed an IOVA, not a physical address: p176
 * and p177 showed every BHI register reading back the value star expects and
 * the status still staying 0, because nothing translated the address the
 * endpoint was asked to fetch. */
#define PCIE_SMMU_PHYS      0x15000000u
#define PCIE_SMMU_SIZE      0x100000u
#define PCIE_SMMU_IOVA      0xa0004000ull
#define PCIE_SMMU_STREAM    0x1c01u
#define PCIE_SMMU_FAULT     0xc00001feu

static vm_offset_t smmu_mmio, smmu_cb, smmu_tables;
static uint32_t smmu_match, smmu_context;
static int smmu_state;

static void
pcie_table_flush(vm_offset_t start, uint32_t size)
{
	vm_offset_t line;

	for (line = start; line < start + size; line += 64) {
		__asm__ volatile ("dc civac, %0" : : "r" (line) : "memory");
	}
	__asm__ volatile ("dsb sy" : : : "memory");
}

static bool
pcie_smmu_setup(void)
{
	uint32_t scr, id0, id1, matches, contexts, s2contexts;
	uint32_t i, hash, smr, s2cr, cbar, cba2r;
	uint64_t *l1, *l2, *l3, root, physical;
	unsigned page;

	if (pcie_dma == 0) {
		printf("pcie: smmu: there is no dma page to translate\n");
		return false;
	}
	smmu_mmio = ml_io_map_unmappable(PCIE_SMMU_PHYS, PCIE_SMMU_SIZE, VM_WIMG_IO);
	if (smmu_mmio == 0) {
		printf("pcie: smmu: cannot map 0x%x\n", PCIE_SMMU_PHYS);
		return false;
	}
	scr = rd(smmu_mmio);
	id0 = rd(smmu_mmio + 0x20);
	id1 = rd(smmu_mmio + 0x24);
	matches = id0 & 255;
	contexts = id1 & 255;
	s2contexts = (id1 >> 16) & 255;
	printf("pcie: smmu: scr 0x%08x idr0 0x%08x idr1 0x%08x (%u matches, %u contexts, %u stage 2) gfsr 0x%08x\n",
	       scr, id0, id1, matches, contexts, s2contexts, rd(smmu_mmio + 0x48));
	if ((scr & 9) || !(scr & (1u << 10)) || !(id0 & (1u << 30)) ||
	    matches == 0 || matches > 255 || contexts == 0 || contexts > 128 ||
	    rd(smmu_mmio + 0x48) != 0) {
		printf("pcie: smmu: the geometry is not the one this code knows\n");
		return false;
	}
	if (kmem_alloc(kernel_map, &smmu_tables, 3 * PAGE_SIZE,
	    KMA_KOBJECT | KMA_ZERO | KMA_DATA, VM_KERN_MEMORY_IOKIT) != KERN_SUCCESS) {
		printf("pcie: smmu: cannot allocate the tables\n");
		return false;
	}
	l1 = (uint64_t *)smmu_tables;
	l2 = (uint64_t *)(smmu_tables + PAGE_SIZE);
	l3 = (uint64_t *)(smmu_tables + 2 * PAGE_SIZE);
	l1[(PCIE_SMMU_IOVA >> 30) & 511] = kvtophys(smmu_tables + PAGE_SIZE) | 3;
	l2[(PCIE_SMMU_IOVA >> 21) & 511] = kvtophys(smmu_tables + 2 * PAGE_SIZE) | 3;
	for (page = 0; page < PCIE_DMA_SIZE / 4096; page++) {
		physical = kvtophys(pcie_dma + page * 4096);
		if (physical == 0) {
			printf("pcie: smmu: page %u has no physical address\n", page);
			return false;
		}
		l3[((PCIE_SMMU_IOVA + page * 4096) >> 12) & 511] =
		    physical | 3ull | (1ull << 6) | (2ull << 8) | (1ull << 10) |
		    (1ull << 11) | (1ull << 53) | (1ull << 54);
	}
	pcie_table_flush(smmu_tables, 3 * PAGE_SIZE);
	printf("pcie: smmu: tables at 0x%llx, iova 0x%llx -> pa 0x%llx, %u pages\n",
	       (unsigned long long)kvtophys(smmu_tables), (unsigned long long)PCIE_SMMU_IOVA,
	       (unsigned long long)kvtophys(pcie_dma), PCIE_DMA_SIZE / 4096);
	/*
	 * The endpoint asks with BDF 01:00.0.  The PARF table turns that into a
	 * relative SID and 0x2c00 bit 0 has to be clear for the table to be used
	 * at all (vendor msm_pcie_config_sid, pci-msm.c:4259; star's
	 * route_endpoint, lemonade_wifi.c:399).
	 */
	hash = requester_hash(0x0100);
	if (hash == 0) {
		printf("pcie: smmu: the requester hash of 0x0100 is zero\n");
		return false;
	}
	for (i = 0; i < 256; i++) {
		wr(parf.base + 0x2000 + 4 * i, 0);
	}
	wr(parf.base + 0x2000 + 4 * hash, 0x01000100);
	wr(parf.base + 0x2c00, rd(parf.base + 0x2c00) & ~1u);
	printf("pcie: smmu: parf sid table: bdf 0x0100 -> hash %u, 0x2000[%u] = 0x%08x, 0x2c00 = 0x%08x\n",
	       hash, hash, rd(parf.base + 0x2000 + 4 * hash), rd(parf.base + 0x2c00));
	smmu_match = matches;
	for (i = 0; i < matches; i++) {
		smr = rd(smmu_mmio + 0x800 + 4 * i);
		if (!(smr & (1u << 31))) {
			smmu_match = i;
			break;
		}
	}
	if (smmu_match == matches) {
		printf("pcie: smmu: every stream is in use\n");
		return false;
	}
	smmu_context = contexts;
	for (i = s2contexts; i < contexts; i++) {
		vm_offset_t cb = smmu_mmio + 0x80000 + 4096 * i;

		if (!(rd(cb) & 1) && !(rd(cb + 0x58) & PCIE_SMMU_FAULT)) {
			smmu_context = i;
			smmu_cb = cb;
			break;
		}
	}
	if (smmu_context == contexts) {
		printf("pcie: smmu: no context bank is free\n");
		return false;
	}
	cbar = rd(smmu_mmio + 0x1000 + 4 * smmu_context);
	cba2r = rd(smmu_mmio + 0x1800 + 4 * smmu_context);
	printf("pcie: smmu: claim match %u context %u for stream 0x%04x (cbar 0x%08x cba2r 0x%08x)\n",
	       smmu_match, smmu_context, PCIE_SMMU_STREAM, cbar, cba2r);
	wr(smmu_cb, 0);
	wr(smmu_mmio + 0x1800 + 4 * smmu_context, 1);
	wr(smmu_mmio + 0x1000 + 4 * smmu_context, (1u << 16) | (3u << 8) | (15u << 12));
	wr(smmu_cb + 0x10, 1u | (1u << 4) | (7u << 15));
	wr(smmu_cb + 0x30, 25u | (1u << 8) | (1u << 10) | (3u << 12) | (1u << 23));
	root = kvtophys(smmu_tables) | ((uint64_t)smmu_context << 48);
	wr(smmu_cb + 0x20, (uint32_t)root);
	wr(smmu_cb + 0x24, (uint32_t)(root >> 32));
	wr(smmu_cb + 0x28, 0);
	wr(smmu_cb + 0x2c, 0);
	wr(smmu_cb + 0x38, 0xf404ff44);
	wr(smmu_cb + 0x3c, 0);
	wr(smmu_cb + 0x610, smmu_context);
	wr(smmu_cb + 0x7f0, 0);
	for (i = 0; i < 10000 && !(rd(smmu_cb + 0x7f4) & 1); i++) {
	}
	printf("pcie: smmu: tlbi ack 0x7f4 = 0x%08x\n", rd(smmu_cb + 0x7f4));
	wr(smmu_cb, 0x1127);
	wr(smmu_mmio + 0xc00 + 4 * smmu_match, smmu_context);
	wr(smmu_mmio + 0x800 + 4 * smmu_match, 0x80000000u | PCIE_SMMU_STREAM);
	smr = rd(smmu_mmio + 0x800 + 4 * smmu_match);
	s2cr = rd(smmu_mmio + 0xc00 + 4 * smmu_match);
	printf("pcie: smmu: readback smr 0x%08x s2cr 0x%08x sctlr 0x%08x tcr 0x%08x ttbr 0x%08x:%08x root 0x%llx\n",
	       smr, s2cr, rd(smmu_cb), rd(smmu_cb + 0x30),
	       rd(smmu_cb + 0x24), rd(smmu_cb + 0x20), (unsigned long long)root);
	if (smr != (0x80000000u | PCIE_SMMU_STREAM) ||
	    (s2cr & 0x300ff) != smmu_context || !(rd(smmu_cb) & 1) ||
	    rd(smmu_cb + 0x20) != (uint32_t)root ||
	    rd(smmu_cb + 0x24) != (uint32_t)(root >> 32)) {
		printf("pcie: smmu: the readback does not match\n");
		return false;
	}
	for (page = 0; page < PCIE_DMA_SIZE / 4096; page++) {
		uint64_t pte = l3[((PCIE_SMMU_IOVA + page * 4096) >> 12) & 511];

		if ((pte & 0x0000fffffffff000ull) != kvtophys(pcie_dma + page * 4096)) {
			printf("pcie: smmu: page %u walks to 0x%llx\n", page, (unsigned long long)pte);
			return false;
		}
	}
	printf("pcie: smmu: %u pages walk from iova 0x%llx to the dma page\n",
	       PCIE_DMA_SIZE / 4096, (unsigned long long)PCIE_SMMU_IOVA);
	return true;
}

"""

anchor = "void\nhakios_pcie_init(void)\n"
assert s.count(anchor) == 1, s.count(anchor)
s = s.replace(anchor, smmu + anchor)

old = "\t\t\t\t/* apply-175: the endpoint can only fetch the image once it is a\n\t\t\t\t * bus master.  star's bhi_request() writes the same 0x6 into\n\t\t\t\t * both the RC's and the endpoint's command register. */"
new = "\t\t\t\t/* apply-176: the endpoint fetches through the SMMU, so claim a\n\t\t\t\t * stream context for SID 0x1c01 before it becomes a bus master\n\t\t\t\t * (star's bhi_request refuses to run until dma_space.owned). */\n\t\t\t\tif (smmu_state == 0) {\n\t\t\t\t\tsmmu_state = pcie_smmu_setup() ? 1 : -1;\n\t\t\t\t}\n\t\t\t\tprintf(\"pcie: 5:   21: smmu state %d\\n\", smmu_state);\n\t\t\t\t/* apply-175: the endpoint can only fetch the image once it is a\n\t\t\t\t * bus master.  star's bhi_request() writes the same 0x6 into\n\t\t\t\t * both the RC's and the endpoint's command register. */"
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

old = "\t\t\t\twr(bar0.base + 0x12c, 0);\n\t\t\t\twr(bar0.base + 0x10c, (uint32_t)(pcie_dma_pa >> 32));\n\t\t\t\twr(bar0.base + 0x108, (uint32_t)pcie_dma_pa);"
new = "\t\t\t\twr(bar0.base + 0x12c, 0);\n\t\t\t\t/* apply-176: star hands PBL the IOVA in its own page table\n\t\t\t\t * (WIFI_DMA_IOVA 0xa0004000), never a physical address. */\n\t\t\t\twr(bar0.base + 0x10c, (uint32_t)(PCIE_SMMU_IOVA >> 32));\n\t\t\t\twr(bar0.base + 0x108, (uint32_t)PCIE_SMMU_IOVA);"
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

io.open(p, "w", encoding="utf-8").write(s)
print("patched")