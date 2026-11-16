import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old_decl = "static uint32_t pcie_mhi_nhwer0;"
assert s.count(old_decl) == 1, ("decl", s.count(old_decl))
s = s.replace(old_decl, "static uint32_t pcie_eridx = 1;\t/* apply-305: which event ring the channels point at */\n" + old_decl, 1)

anchor = 'if (PE_parse_boot_argn("pcie_mhi_nhwer0", &d11, sizeof(d11))) {'
assert s.count(anchor) == 1, ("parse", s.count(anchor))
add = '''{
								uint32_t d12 = pcie_eridx;

								if (PE_parse_boot_argn("pcie_eridx", &d12, sizeof(d12))) {
									pcie_eridx = d12;
								}
							}
							'''
s = s.replace(anchor, add + anchor, 1)

old_wr = "wr(pcie_dma_extra + o3 + 0x08, 1u);"
assert s.count(old_wr) == 1, ("wr", s.count(old_wr))
s = s.replace(old_wr, "wr(pcie_dma_extra + o3 + 0x08, pcie_eridx);", 1)

io.open(p, "w", encoding="utf-8").write(s)
print("apply-305 applied")