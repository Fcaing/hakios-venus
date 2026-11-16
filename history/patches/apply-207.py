import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

anchor = '\t\tprintf("pcie: 5:   21: bhi after: status 0x%08x (top %u, ee %u) mhi 0x%08x err 0x%08x\\n",'
assert s.count(anchor) == 1, s.count(anchor)

block = r'''		{
			/* apply-207: star's inspect table -- 23 GCC clocks and the six GPIOs,
			 * read after the port is fully up so the values are final. */
			static const struct { const char *name; uint32_t offset; } clocks[] = {
				{"gdsc", 0x6b004}, {"core_reset", 0x6b000}, {"phy_reset", 0x6c01c},
				{"vote0", 0x52000}, {"vote1", 0x52008}, {"collapse_vote", 0x52128},
				{"cfg_ahb", 0x6b024}, {"aux", 0x6b028}, {"mstr_axi", 0x6b01c},
				{"slv_axi", 0x6b014}, {"q2a_axi", 0x6b010}, {"pipe", 0x6b030},
				{"clkref", 0x8c004}, {"rchng", 0x6b038}, {"tbu", 0x9000c},
				{"ddrss", 0x8d080}, {"aggre0", 0x6b080}, {"aggre1", 0x8d084},
				{"aux_src", 0x6b058}, {"aux_cfg", 0x6b05c}, {"pipe_src", 0x6b054},
				{"rchng_src", 0x6b03c}, {"rchng_cfg", 0x6b040}
			};
			static const uint32_t gpios[] = { 64, 65, 94, 95, 96, 153 };
			uint32_t k;
			for (k = 0; k < sizeof(clocks) / sizeof(clocks[0]); k++) {
				printf("pcie: 5:   21: gcc %-13s 0x%05x = 0x%08x\n", clocks[k].name,
				    clocks[k].offset, rd(gcc.base + clocks[k].offset));
			}
			for (k = 0; k < sizeof(gpios) / sizeof(gpios[0]); k++) {
				uint32_t pin = gpios[k] * 0x1000;
				printf("pcie: 5:   21: gpio %3u cfg 0x%08x io 0x%08x irq 0x%08x\n", gpios[k],
				    rd(tlmm.base + pin), rd(tlmm.base + pin + 4), rd(tlmm.base + pin + 8));
			}
		}
'''
s = s.replace(anchor, block + anchor, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("ok apply-207")