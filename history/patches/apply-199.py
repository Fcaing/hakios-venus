import io

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old = """				printf("pcie: 5:   21: bhi before: soc 0x%08x ee 0x%08x mhi 0x%08x status 0x%08x err 0x%08x\\n","""
new = """				/*
				 * apply-199: p196 showed both inbound iATU windows are empty
				 * on this phone, unlike every device that has reported a
				 * working BHI. Program inbound 0 as a plain memory window:
				 * 0xa0000000..0xa007ffff in the endpoint's space turns into the
				 * staging page in ours. ctrl2 has no BAR-mode bit, so this is a
				 * DMA window and not a PIO one.
				 */
				if (pcie_dma_pa != 0) {
					wr(dbi.base + 0x1100, 0x00000000u);
					wr(dbi.base + 0x1104, 0x00000000u);
					wr(dbi.base + 0x1108, 0xa0000000u);
					wr(dbi.base + 0x110c, 0x00000000u);
					wr(dbi.base + 0x1110, 0xa007ffffu);
					wr(dbi.base + 0x1114, (uint32_t)pcie_dma_pa);
					wr(dbi.base + 0x1118, (uint32_t)(pcie_dma_pa >> 32));
					wr(dbi.base + 0x1104, 0x80000000u);
					printf("pcie: 5:   21: inbound 0xa0000000-0xa007ffff -> 0x%llx, "
					    "readback %08x %08x %08x %08x %08x %08x %08x\\n",
					    pcie_dma_pa,
					    rd(dbi.base + 0x1100), rd(dbi.base + 0x1104), rd(dbi.base + 0x1108),
					    rd(dbi.base + 0x110c), rd(dbi.base + 0x1110), rd(dbi.base + 0x1114),
					    rd(dbi.base + 0x1118));
				}
				printf("pcie: 5:   21: bhi before: soc 0x%08x ee 0x%08x mhi 0x%08x status 0x%08x err 0x%08x\\n","""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("patched")