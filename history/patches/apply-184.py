import io

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

# the SMMU refused any non-zero mask, so go back to the exact 0x1c01 match.
old = """	wr(smmu_mmio + 0x800 + 4 * smmu_match, 0x80000000u | (1u << 16) | 0x1c00u);"""
new = """	wr(smmu_mmio + 0x800 + 4 * smmu_match, 0x80000000u | PCIE_SMMU_STREAM);"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

old = """	if (smr != (0x80000000u | (1u << 16) | 0x1c00u) ||"""
new = """	if (smr != (0x80000000u | PCIE_SMMU_STREAM) ||"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

# sweep candidate stream ids in a single run.
old = """				if (smmu_state == 1) {
					uint64_t guard = PCIE_SMMU_IOVA + PCIE_DMA_SIZE;"""
new = """				if (smmu_state == 1) {
					/*
					 * apply-184: the SMMU takes only exact matches (a one
					 * bit mask read back zero), so sweep the plausible
					 * stream ids in one run and watch for the fault that
					 * proves which one the endpoint really uses.
					 */
					static const uint32_t streams[] = {
						0x1c00u, 0x1c01u, 0x1c02u, 0x1c04u,
						0x1c08u, 0x1c10u, 0x1c20u, 0x1c40u,
					};
					uint32_t k;

					for (k = 0; k < sizeof(streams) / sizeof(streams[0]); k++) {
						uint64_t guard = PCIE_SMMU_IOVA + PCIE_DMA_SIZE;
						uint32_t fsr = 0, i;

						wr(smmu_mmio + 0x800 + 4 * smmu_match, 0x80000000u | streams[k]);
						wr(smmu_cb + 0x7f0, 0);
						sleep_ms(2);
						wr(bar0.base + 0x12c, 0);
						wr(bar0.base + 0x10c, (uint32_t)(guard >> 32));
						wr(bar0.base + 0x108, (uint32_t)guard);
						wr(bar0.base + 0x110, 4096);
						wr(bar0.base + 0x118, 1);
						for (i = 0; i < 500; i++) {
							fsr = rd(smmu_cb + 0x58);
							if ((fsr & PCIE_SMMU_FAULT) || rd(smmu_mmio + 0x48) != 0) {
								break;
							}
							sleep_ms(1);
						}
						printf("pcie: 5:   21: stream 0x%04x: after %u ms fsr 0x%08x far 0x%08x:0x%08x bhi 0x%08x ee 0x%08x\\n",
						       streams[k], i, fsr, rd(smmu_cb + 0x60), rd(smmu_cb + 0x64),
						       rd(bar0.base + 0x12c), rd(bar0.base + 0x128));
						wr(smmu_cb + 0x58, fsr & PCIE_SMMU_FAULT);
					}
					/* Leave the endpoint stream in place for the real transfer. */
					wr(smmu_mmio + 0x800 + 4 * smmu_match, 0x80000000u | PCIE_SMMU_STREAM);
					wr(smmu_cb + 0x7f0, 0);
					sleep_ms(2);
					guard = PCIE_SMMU_IOVA + PCIE_DMA_SIZE;"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

io.open(p, "w", encoding="utf-8").write(s)
print("patched")