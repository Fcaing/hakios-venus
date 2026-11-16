import io

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old = """				printf("pcie: 5:   21: bar0 0x128 = 0x%08x (star wants 0)\\n", rd(bar0.base + 0x128));"""
new = """				printf("pcie: 5:   21: bar0 0x128 = 0x%08x (star wants 0)\\n", rd(bar0.base + 0x128));
				/*
				 * apply-178: star's dma_fault_probe (lemonade_wifi.c:731).  Ask
				 * PBL to read the page right after the mapped window.  If the
				 * endpoint's SID really reaches the SMMU, the context bank has
				 * to answer with a translation fault and put that address in
				 * FAR.  Without that fault nothing downstream can be trusted.
				 */
				if (smmu_state == 1) {
					uint64_t guard = PCIE_SMMU_IOVA + PCIE_DMA_SIZE;
					uint32_t fsr = 0, i;

					wr(bar0.base + 0x12c, 0);
					wr(bar0.base + 0x10c, (uint32_t)(guard >> 32));
					wr(bar0.base + 0x108, (uint32_t)guard);
					wr(bar0.base + 0x110, 4096);
					wr(bar0.base + 0x118, 1);
					for (i = 0; i < 2000; i++) {
						fsr = rd(smmu_cb + 0x58);
						if ((fsr & PCIE_SMMU_FAULT) || rd(smmu_mmio + 0x48) != 0) {
							break;
						}
						sleep_ms(1);
					}
					printf("pcie: 5:   21: guard test: after %u ms fsr 0x%08x far 0x%08x:0x%08x sid 0x%08x gfsr 0x%08x bhi 0x%08x ee 0x%08x\\n",
					       i, fsr, rd(smmu_cb + 0x60), rd(smmu_cb + 0x64),
					       rd(smmu_mmio + 0x1400 + 4 * smmu_context) & 0xffff,
					       rd(smmu_mmio + 0x48), rd(bar0.base + 0x12c),
					       rd(bar0.base + 0x128));
					/* Clear the fault so the real transfer starts clean. */
					wr(smmu_cb + 0x58, fsr & PCIE_SMMU_FAULT);
				}"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

old = """				wr(bar0.base + 0x118, 1);
				sleep_ms(300);"""
new = """				wr(bar0.base + 0x118, 1);
				/* apply-178: star polls 1000 times with 10 ms; stay short
				 * enough not to hang the boot path. */
				{
					uint32_t i;

					for (i = 0; i < 30; i++) {
						uint32_t st = rd(bar0.base + 0x12c);

						if (((st >> 30) == 2 && rd(bar0.base + 0x128) == 1) ||
						    (st >> 30) == 3) {
							break;
						}
						sleep_ms(100);
					}
				}"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

io.open(p, "w", encoding="utf-8").write(s)
print("patched")