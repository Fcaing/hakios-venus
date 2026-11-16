import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

d = "static uint32_t pcie_trap_buf;"
assert s.count(d) == 1
s = s.replace(d, d + "\nstatic uint32_t pcie_tre_flags = 0x00020200;\nstatic uint32_t pcie_tre_count = 2;")

a = """								d2 = 0;
								if (PE_parse_boot_argn("pcie_trap_buf", &d2, sizeof(d2))) {
									pcie_trap_buf = d2;
								}"""
assert s.count(a) == 1
s = s.replace(a, a + """
								d2 = 0;
								if (PE_parse_boot_argn("pcie_tre_flags", &d2, sizeof(d2))) {
									pcie_tre_flags = d2;
								}
								d2 = 0;
								if (PE_parse_boot_argn("pcie_tre_count", &d2, sizeof(d2))) {
									pcie_tre_count = d2;
								}""")

old = """						wr(pcie_dma_extra + dring_off + 0x000c, 0x00020200u);
						wr(pcie_dma_extra + dring_off + 0x0014, 0u);
						wr(pcie_dma_extra + dring_off + 0x0018, 0x00001000u);
						wr(pcie_dma_extra + dring_off + 0x001c, 0x00020200u);
						wr(pcie_dma_extra + dch * 0x2c + 0x24, (uint32_t)trewp);"""
assert s.count(old) == 1
s = s.replace(old, """						wr(pcie_dma_extra + dring_off + 0x000c, pcie_tre_flags);
						wr(pcie_dma_extra + dring_off + 0x0014, 0u);
						wr(pcie_dma_extra + dring_off + 0x0018, 0x00001000u);
						wr(pcie_dma_extra + dring_off + 0x001c, pcie_tre_flags);
						trewp = dring + (uint64_t)(pcie_tre_count != 0u ? pcie_tre_count : 1u) * 0x10u;
						wr(pcie_dma_extra + dch * 0x2c + 0x24, (uint32_t)trewp);""")

io.open(p, "w", encoding="utf-8").write(s)
print("apply-320 written")