import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

# 1. declare the boot-arg variable next to the other mhi switches
old_decl = "static uint32_t pcie_mhi_data;"
if old_decl not in s:
    old_decl = "static uint32_t pcie_mhi_late0;"
assert s.count(old_decl) == 1, ("decl anchor", s.count(old_decl))
s = s.replace(old_decl, "static uint32_t pcie_mhi_nhwer0 = 0;\n" + old_decl, 1)

# 2. parse it
anchor = 'PE_parse_boot_argn("pcie_mhi_data", &d2, sizeof(d2));'
assert s.count(anchor) == 1, ("parse anchor", s.count(anchor))
parse_add = '''{
		uint32_t d10 = pcie_mhi_nhwer0;
		if (PE_parse_boot_argn("pcie_mhi_nhwer0", &d10, sizeof(d10))) {
			pcie_mhi_nhwer0 = d10;
		}
	}
	'''
s = s.replace(anchor, parse_add + anchor, 1)

# 3. apply it right before the data TRE is written
anchor2 = "wr(pcie_dma_extra + 0xc000, (uint32_t)datiova);"
assert s.count(anchor2) == 1, ("tre anchor", s.count(anchor2))
block = '''{
		uint32_t cf4 = rd(bar0.base + 0x10);
		if (pcie_mhi_nhwer0 != 0) {
			wr(bar0.base + 0x10, (cf4 & 0x0000ffffu) | (3u << 16));
			printf("apply-304 mhicfg 0x%08x -> 0x%08x (nhwer cleared, as vendor)\\n",
			    cf4, rd(bar0.base + 0x10));
		}
	}
	'''
s = s.replace(anchor2, block + anchor2, 1)

io.open(p, "w", encoding="utf-8").write(s)
print("apply-304 applied")