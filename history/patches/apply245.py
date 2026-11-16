import io, sys
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
before = s

def sub(old, new, what):
    global s
    assert s.count(old) == 1, "%s: found %d" % (what, s.count(old))
    s = s.replace(old, new)

# 1) the new switch
lines = s.split("\n")
for i, ln in enumerate(lines):
    if "static uint32_t pcie_star_mask = 0x1fu;" in ln:
        lines.insert(i + 1, "static uint32_t pcie_headonly;	/* apply-245: map only page 0 of the staging window */")
        break
else:
    sys.exit("no star_mask static")
s = "\n".join(lines)

# 2) parse the boot argument where the tables are built
sub("""static bool
pcie_smmu_setup(void)
{
	uint32_t scr, id0, id1, matches, contexts, s2contexts;""",
"""static bool
pcie_smmu_setup(void)
{
	uint32_t scr, id0, id1, matches, contexts, s2contexts;
	uint32_t headonly = 0;

	if (PE_parse_boot_argn("pcie_headonly", &headonly, sizeof(headonly))) {
		pcie_headonly = headonly;
	}""", "smmu setup header")

# 3) map only page 0 when asked
sub("""	for (page = 0; page < PCIE_DMA_SIZE / 4096; page++) {
		physical = kvtophys(pcie_dma + page * 4096);""",
"""	for (page = 0; page < PCIE_DMA_SIZE / 4096; page++) {
		/*
		 * apply-245: hand the PBL nothing but the first page -- the ELF
		 * header and the program header table -- and leave the segment
		 * bodies unmapped.  A PBL that really loads segments has to
		 * fault here, and the FAR says which file offset it reached.
		 */
		if (pcie_headonly != 0 && page != 0) {
			continue;
		}
		physical = kvtophys(pcie_dma + page * 4096);""", "staging page loop")

sub("""	}
	if (pcie_dma_vec_pa != 0) {""",
"""	}
	if (pcie_headonly != 0) {
		printf("pcie: smmu: apply-245 headonly: only page 0 of the staging window is mapped\\n");
	}
	if (pcie_dma_vec_pa != 0) {""", "headonly note")

# 4) measure star's reset pulses instead of assuming them
sub("""	if (pcie_star_mask & 4u) {
		sleep_us(1000);
		wr(gcc.base + 0x6b000, rd(gcc.base + 0x6b000) | 1u);
		sleep_us(1000);
		wr(gcc.base + 0x6b000, rd(gcc.base + 0x6b000) & ~1u);
		wr(gcc.base + 0x6c01c, rd(gcc.base + 0x6c01c) | 1u);
		sleep_us(1000);
		wr(gcc.base + 0x6c01c, rd(gcc.base + 0x6c01c) & ~1u);
		printf("pcie: 3:   star stage 5 (before parf, as star does): the root and the phy pulsed (0x6b000 0x%08x, 0x6c01c 0x%08x)\\n",
		       rd(gcc.base + 0x6b000), rd(gcc.base + 0x6c01c));
	}""",
"""	if (pcie_star_mask & 4u) {
		uint32_t t, pulse = 1000;

		PE_parse_boot_argn("pcie_pulse_us", &pulse, sizeof(pulse));
		sleep_us(1000);
		/*
		 * apply-245: star's change_gcc() raises the bit and then waits for
		 * the block to clear it again.  Measure that here instead of
		 * assuming a millisecond, so the two runs can be compared.
		 */
		wr(gcc.base + 0x6b000, rd(gcc.base + 0x6b000) | 1u);
		for (t = 0; t < 5000; t++) {
			if ((rd(gcc.base + 0x6b000) & 1u) == 0) {
				break;
			}
			sleep_us(1);
		}
		printf("pcie: 3:   apply-245: 0x6b000 raised, self-cleared after %u us -> 0x%08x\\n",
		       t, rd(gcc.base + 0x6b000));
		wr(gcc.base + 0x6b000, rd(gcc.base + 0x6b000) & ~1u);
		sleep_us(pulse);
		printf("pcie: 3:   apply-245: 0x6b000 after a %u us pause: 0x%08x\\n",
		       pulse, rd(gcc.base + 0x6b000));
		wr(gcc.base + 0x6c01c, rd(gcc.base + 0x6c01c) | 1u);
		for (t = 0; t < 5000; t++) {
			if ((rd(gcc.base + 0x6c01c) & 1u) == 0) {
				break;
			}
			sleep_us(1);
		}
		printf("pcie: 3:   apply-245: 0x6c01c raised, self-cleared after %u us -> 0x%08x\\n",
		       t, rd(gcc.base + 0x6c01c));
		wr(gcc.base + 0x6c01c, rd(gcc.base + 0x6c01c) & ~1u);
		sleep_us(pulse);
		printf("pcie: 3:   apply-245: 0x6c01c after a %u us pause: 0x%08x\\n",
		       pulse, rd(gcc.base + 0x6c01c));
	}""", "stage 5 pulse block")

# 5) the value of dbi 0x80 before the link trains, to match star's log
sub("""			perst(false);
			sleep_ms(100);
			gen1_config();""",
"""			printf("pcie: 4:   apply-245: before PERST#: DBI 0x80 = 0x%08x, DBI 0x04 = 0x%08x\\n",
			       rd(dbi.base + 0x80), rd(dbi.base + 0x4));
			perst(false);
			sleep_ms(100);
			gen1_config();""", "pre perst print")

# 6) after the doorbell, watch for the fault a segment load would cause
sub("""wr(bar0.base + 0x118, db);
					printf("pcie: 5:   21: bhi doorbell 0x%08x\\n", db);""",
"""wr(bar0.base + 0x118, db);
					printf("pcie: 5:   21: bhi doorbell 0x%08x\\n", db);
					if (pcie_headonly != 0 && smmu_state == 1) {
						uint32_t k, fsr = 0, global = 0;
						uint64_t far;

						for (k = 0; k < 600; k++) {
							fsr = rd(smmu_cb + 0x58);
							global = rd(smmu_mmio + 0x48);
							if ((fsr & 2u) != 0 || global != 0) {
								break;
							}
							if ((rd(bar0.base + 0x12c) >> 30) == 2) {
								break;
							}
							sleep_ms(5);
						}
						far = ((uint64_t)rd(smmu_cb + 0x64) << 32) |
						    (uint64_t)rd(smmu_cb + 0x60);
						printf("pcie: 5:   21: apply-245 headonly: after %u ms fsr 0x%08x far 0x%llx gfsr 0x%08x bhi 0x%08x ee 0x%08x\\n",
						    k * 5, fsr, (unsigned long long)far, global,
						    rd(bar0.base + 0x12c), rd(bar0.base + 0x128));
					}""", "headonly watch")

io.open(p, "w", encoding="utf-8").write(s)
print("apply-245 applied: %d -> %d bytes" % (len(before), len(s)))