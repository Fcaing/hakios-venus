import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

if "pcie_data_ch" not in s:
    old_decl = "static uint32_t pcie_eridx = 1;"
    assert s.count(old_decl) == 1, ("decl", s.count(old_decl))
    s = s.replace(old_decl, "static uint32_t pcie_data_ch = 20;\t/* apply-306: which channel carries our first tre */\n" + old_decl, 1)

    anchor = 'if (PE_parse_boot_argn("pcie_eridx", &d12, sizeof(d12))) {'
    assert s.count(anchor) == 1, ("parse", s.count(anchor))
    add = '''{
								uint32_t d13 = pcie_data_ch;

								if (PE_parse_boot_argn("pcie_data_ch", &d13, sizeof(d13))) {
									pcie_data_ch = d13;
								}
							}
							'''
    s = s.replace(anchor, add + anchor, 1)

start = s.index("if (pcie_mhi_data != 0 && smmu_state == 1) {")
end = s.index("if (pcie_mhi_watch != 0 && smmu_state == 1 && pcie_dma_extra != 0) {")
blk = s[start:end]

head_anchor = "\t\t\t\t\t\tuint32_t d9;\n"
assert blk.count(head_anchor) == 1, ("head", blk.count(head_anchor))
head = '''\t\t\t\t\t\tuint32_t dch = pcie_data_ch;
						uint32_t didx = (dch == 0u) ? 0u : (dch == 1u) ? 1u : (dch == 4u) ? 2u : (dch == 5u) ? 3u : (dch == 20u) ? 4u : 5u;
						uint32_t dring_off = 0x8000u + didx * 0x1000u;
						uint64_t dring = PCIE_EXTRA_IOVA + dring_off;
'''
blk = blk.replace(head_anchor, head + head_anchor, 1)

# the tre ring and its host-side offset
blk = blk.replace("PCIE_EXTRA_IOVA + 0xc010", "dring + 0x10")
blk = blk.replace("PCIE_EXTRA_IOVA + 0xc000", "dring")
blk = blk.replace("pcie_dma_extra + 0xc00", "pcie_dma_extra + dring_off + 0x000")
# the channel context and the doorbell
blk = blk.replace("20 * 0x2c", "dch * 0x2c")
blk = blk.replace("0x300 + 20 * 8", "0x300 + dch * 8")
# widen the flush so the context block is covered too
blk = blk.replace("for (d9 = 0x3000; d9 < 0xd000; d9 += 64) {", "for (d9 = 0x0000; d9 < 0xe000; d9 += 64) {")

s = s[:start] + blk + s[end:]
io.open(p, "w", encoding="utf-8").write(s)
print("apply-306 applied")