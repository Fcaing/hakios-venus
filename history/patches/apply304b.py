import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old_decl = "static uint32_t pcie_mhi_data;"
assert s.count(old_decl) == 1, ("decl", s.count(old_decl))
s = s.replace(old_decl, "static uint32_t pcie_mhi_nhwer0;\t/* apply-304: clear nhwer like the vendor does */\n" + old_decl, 1)

anchor = 'if (PE_parse_boot_argn("pcie_mhi_data", &d2, sizeof(d2))) {'
assert s.count(anchor) == 1, ("parse", s.count(anchor))
parse_add = '''{
								uint32_t d11 = pcie_mhi_nhwer0;

								if (PE_parse_boot_argn("pcie_mhi_nhwer0", &d11, sizeof(d11))) {
									pcie_mhi_nhwer0 = d11;
								}
							}
							'''
s = s.replace(anchor, parse_add + anchor, 1)

anchor2 = "wr(pcie_dma_extra + 0xc000, (uint32_t)datiova);"
assert s.count(anchor2) == 1, ("tre", s.count(anchor2))
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