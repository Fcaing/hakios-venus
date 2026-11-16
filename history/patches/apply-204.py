import io
import sys

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
orig = s


def sub1(old, new, what):
    global s
    if s.count(old) != 1:
        print("FAIL %s: count=%d" % (what, s.count(old)))
        sys.exit(1)
    s = s.replace(old, new, 1)
    print("ok %s" % what)


# 1. new macro next to the other SMMU ones
sub1(
    "#define PCIE_SMMU_FAULT     0xc00001feu\n",
    "#define PCIE_SMMU_FAULT     0xc00001feu\n"
    "/* apply-204: one more 4 KiB page right past the staging area, holding the\n"
    " * BHIE vector table.  The endpoint reads vectors from here, so this page\n"
    " * has to be reachable through the same context bank. */\n"
    "#define PCIE_SMMU_VEC_IOVA  0xa0084000ull\n",
    "macro",
)

# 2. variables
sub1(
    "static uint64_t pcie_dma_pa;\n",
    "static uint64_t pcie_dma_pa;\n"
    "static vm_offset_t pcie_dma_vec;\n"
    "static uint64_t pcie_dma_vec_pa;\n",
    "vars",
)

# 3. allocate the vector page in dma_init, right after the staging page
sub1(
    """		} else {
			printf("pcie: dma init: kmem_alloc_contig -> kr %d, va 0x%llx\\n",
			       kr, (unsigned long long)buffer);
		}
	}
}
""",
    """		} else {
			printf("pcie: dma init: kmem_alloc_contig -> kr %d, va 0x%llx\\n",
			       kr, (unsigned long long)buffer);
		}
		/*
		 * apply-204: the BHIE vector table needs a page of its own; the
		 * staging page is filled with firmware from byte zero.  Taken at
		 * the same early point, for the same reason as the staging page.
		 */
		if (pcie_dma_pa != 0) {
			vm_offset_t vbuf = 0;

			kr = kmem_alloc_contig(kernel_map, &vbuf, PAGE_SIZE, PAGE_MASK, 0, 0,
			    KMA_KOBJECT | KMA_ZERO | KMA_DATA, VM_KERN_MEMORY_IOKIT);
			if (kr == KERN_SUCCESS && vbuf != 0) {
				pcie_dma_vec = vbuf;
				pcie_dma_vec_pa = kvtophys(vbuf);
				printf("pcie: dma init: vector page at 0x%llx, pa 0x%llx\\n",
				       (unsigned long long)pcie_dma_vec,
				       (unsigned long long)pcie_dma_vec_pa);
			} else {
				printf("pcie: dma init: vector page -> kr %d, va 0x%llx\\n",
				       kr, (unsigned long long)vbuf);
			}
		}
	}
}
""",
    "alloc vec",
)

# 4. map the vector page in the same L3 table as the staging area
sub1(
    """	pcie_table_flush(smmu_tables, 3 * PAGE_SIZE);
""",
    """	if (pcie_dma_vec_pa != 0) {
		l3[(PCIE_SMMU_VEC_IOVA >> 12) & 511] =
		    pcie_dma_vec_pa | 3ull | (1ull << 6) | (2ull << 8) | (1ull << 10) |
		    (1ull << 11) | (1ull << 53) | (1ull << 54);
		printf("pcie: smmu: vector page iova 0x%llx -> pa 0x%llx\\n",
		       (unsigned long long)PCIE_SMMU_VEC_IOVA,
		       (unsigned long long)pcie_dma_vec_pa);
	}
	pcie_table_flush(smmu_tables, 3 * PAGE_SIZE);
""",
    "map vec",
)

# 5. replace the BHIE experiment with a real vector-table load
old_bhie_start = """				{
					uint32_t st;

					printf("pcie: 5:   21: bhie soc 0x%08x status 0x%08x\\n",
					       rd(bar0.base + 0x224 + 0x00), rd(bar0.base + 0x224 + 0x44));
"""
idx = s.find(old_bhie_start)
if idx < 0:
    print("FAIL bhie start")
    sys.exit(1)
end_marker = """					pcie_note("bhie 0x%08x; ", st);
				}
"""
idx2 = s.find(end_marker, idx)
if idx2 < 0:
    print("FAIL bhie end")
    sys.exit(1)
idx2 += len(end_marker)

new_bhie = """				/*
				 * apply-204: mhi_fw_load_bhie() does not point the
				 * endpoint at the image, it points it at a table of
				 * {u64 dma_addr; u64 size} entries living in DMA
				 * memory.  Every earlier attempt handed TXVECADDR
				 * the image itself, so PBL read firmware bytes as
				 * vectors and dropped the transfer.  Build a real
				 * table: one entry, the staging page, 512 KiB.
				 */
				{
					uint32_t st = 0, i, seq;
					vm_offset_t vec;

					if (pcie_dma_vec_pa == 0 || pcie_dma_pa == 0) {
						printf("pcie: 5:   21: bhie: no vector page, skipping\\n");
					} else {
						/* p134: the kernel VA from kmem_alloc_contig is
						 * not writable at this point; p163 showed the
						 * unmappable alias is.  Always map. */
						vec = ml_io_map_unmappable((vm_offset_t)pcie_dma_vec_pa,
						    PAGE_SIZE, VM_WIMG_IO);
						wr(vec + 0, (uint32_t)PCIE_SMMU_IOVA);
						wr(vec + 4, (uint32_t)(PCIE_SMMU_IOVA >> 32));
						wr(vec + 8, (uint32_t)PCIE_DMA_SIZE);
						wr(vec + 12, 0);
						__asm__ volatile ("dc civac, %0" : : "r" (vec) : "memory");
						__asm__ volatile ("dsb sy" : : : "memory");
						printf("pcie: 5:   21: bhie vec at 0x%llx (pa 0x%llx) -> iova 0x%llx size 0x%x, readback 0x%08x 0x%08x 0x%08x\\n",
						       (unsigned long long)vec,
						       (unsigned long long)pcie_dma_vec_pa,
						       (unsigned long long)PCIE_SMMU_VEC_IOVA,
						       (unsigned)PCIE_DMA_SIZE,
						       rd(vec + 0), rd(vec + 4), rd(vec + 8));
						wr(bar0.base + 0x224 + 0x44, 0);
						wr(bar0.base + 0x224 + 0x30,
						    (uint32_t)(PCIE_SMMU_VEC_IOVA >> 32));
						wr(bar0.base + 0x224 + 0x2c,
						    (uint32_t)PCIE_SMMU_VEC_IOVA);
						wr(bar0.base + 0x224 + 0x34, 16);
						{
							static uint32_t seed = 0x0badf00du;

							seed = seed * 1103515245u + 12345u;
							seq = (seed >> 2) & 0x3fffffffu;
							if (seq == 0) {
								seq = 1;
							}
						}
						printf("pcie: 5:   21: bhie db 0x%08x, addr 0x%08x:%08x size %u\\n",
						       seq, rd(bar0.base + 0x224 + 0x30),
						       rd(bar0.base + 0x224 + 0x2c),
						       rd(bar0.base + 0x224 + 0x34));
						wr(bar0.base + 0x224 + 0x3c, seq);
						for (i = 0; i < 100; i++) {
							st = rd(bar0.base + 0x224 + 0x44);
							if ((st >> 30) == 2 || (st >> 30) == 3) {
								break;
							}
							sleep_ms(50);
						}
						printf("pcie: 5:   21: bhie after %u polls: status 0x%08x (top %u, seq 0x%08x), ee 0x%08x\\n",
						       i, st, st >> 30, st & 0x3fffffffu,
						       rd(bar0.base + 0x128));
						pcie_note("bhie 0x%08x; ", st);
					}
				}
"""
s = s[:idx] + new_bhie + s[idx2:]
print("ok bhie block")

if s == orig:
    print("FAIL nothing changed")
    sys.exit(1)

io.open(p, "w", encoding="utf-8").write(s)
print("written")
