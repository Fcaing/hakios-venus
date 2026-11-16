import io

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old = """				printf("pcie: 5:   21: bhi before: soc 0x%08x ee 0x%08x mhi 0x%08x status 0x%08x err 0x%08x\\n","""
new = """				/*
				 * apply-197: in the unrolled iATU layout the inbound windows
				 * live at (region << 9) | BIT(8) -- dbi + 0x1100 for inbound 0.
				 * Device DMA needs one of those, not an outbound window.
				 */
				printf("pcie: 5:   21: iatu inbound 0 (dbi+0x1100): "
				    "%08x %08x %08x %08x %08x %08x %08x\\n",
				    rd(dbi.base + 0x1100), rd(dbi.base + 0x1104), rd(dbi.base + 0x1108),
				    rd(dbi.base + 0x110c), rd(dbi.base + 0x1110), rd(dbi.base + 0x1114),
				    rd(dbi.base + 0x1118));
				printf("pcie: 5:   21: iatu inbound 1 (dbi+0x1300): "
				    "%08x %08x %08x %08x %08x %08x %08x\\n",
				    rd(dbi.base + 0x1300), rd(dbi.base + 0x1304), rd(dbi.base + 0x1308),
				    rd(dbi.base + 0x130c), rd(dbi.base + 0x1310), rd(dbi.base + 0x1314),
				    rd(dbi.base + 0x1318));
				printf("pcie: 5:   21: bhi before: soc 0x%08x ee 0x%08x mhi 0x%08x status 0x%08x err 0x%08x\\n","""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("patched")