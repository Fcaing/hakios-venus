import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

d = "static uint32_t pcie_wake2 = 1;"
assert s.count(d) == 1
s = s.replace(d, d + "\nstatic uint32_t pcie_trap_buf;\t/* apply-318: point the data buffer at nothing */")

a = """								d2 = 0;
								if (PE_parse_boot_argn("pcie_wake2", &d2, sizeof(d2))) {
									pcie_wake2 = d2;
								}"""
assert s.count(a) == 1
s = s.replace(a, a + """
								d2 = 0;
								if (PE_parse_boot_argn("pcie_trap_buf", &d2, sizeof(d2))) {
									pcie_trap_buf = d2;
								}""")

old = """						wr(pcie_dma_extra + dring_off + 0x0000, (uint32_t)(PCIE_EXTRA_IOVA + 0xe000u));
						wr(pcie_dma_extra + dring_off + 0x0004, 0u);
						wr(pcie_dma_extra + dring_off + 0x0008, 0x00001000u);
						wr(pcie_dma_extra + dring_off + 0x000c, 0x00020200u);
						wr(pcie_dma_extra + dring_off + 0x0010, (uint32_t)(PCIE_EXTRA_IOVA + 0xf000u));"""
assert s.count(old) == 1
new = """						/* apply-318: with pcie_trap_buf the ring stays valid but the
						 * buffer it points at has no translation at all.  If the device
						 * really consumes the TRE it must fault on that buffer, which
						 * separates "never takes the TRE" from "takes it but never
						 * writes rp back". */
						{
							uint32_t b0 = (uint32_t)(PCIE_EXTRA_IOVA + 0xe000u);
							uint32_t b1 = (uint32_t)(PCIE_EXTRA_IOVA + 0xf000u);

							if (pcie_trap_buf != 0) {
								b0 = 0xa0100000u;
								b1 = 0xa0101000u;
							}
							wr(pcie_dma_extra + dring_off + 0x0000, b0);
							wr(pcie_dma_extra + dring_off + 0x0010, b1);
						}
						wr(pcie_dma_extra + dring_off + 0x0004, 0u);
						wr(pcie_dma_extra + dring_off + 0x0008, 0x00001000u);
						wr(pcie_dma_extra + dring_off + 0x000c, 0x00020200u);"""
s = s.replace(old, new)

old2 = """						printf("pcie: 5:   21: apply-292 send: tre ptr 0x%08x len 0x%08x dw1 0x%08x ch20 wp 0x%08x\\n","""
assert s.count(old2) == 1
s = s.replace(old2, """						if (pcie_trap_buf != 0) {
							wr(smmu_cb + 0x58, rd(smmu_cb + 0x58));
							wr(smmu_mmio + 0x48, rd(smmu_mmio + 0x48));
						}
						printf("pcie: 5:   21: apply-292 send: tre ptr 0x%08x len 0x%08x dw1 0x%08x ch20 wp 0x%08x\\n",""")

old3 = """						/* apply-312: point the ring at an address that has no mapping at all."""
assert s.count(old3) == 1
s = s.replace(old3, """						if (pcie_trap_buf != 0) {
							uint32_t tw;

							for (tw = 0; tw < 200; tw++) {
								if (rd(smmu_cb + 0x58) & 2u) {
									break;
								}
								sleep_ms(5);
							}
							printf("pcie: 5:   21: apply-318 trap buf after %u ms: fsr 0x%08x far 0x%08x:%08x gfsr 0x%08x ch20 rp 0x%08x\\n",
							    tw * 5, rd(smmu_cb + 0x58), rd(smmu_cb + 0x64), rd(smmu_cb + 0x60),
							    rd(smmu_mmio + 0x48), rd(pcie_dma_extra + dch * 0x2c + 0x1c));
						}
						/* apply-312: point the ring at an address that has no mapping at all.""")

io.open(p, "w", encoding="utf-8").write(s)
print("apply-318 written")