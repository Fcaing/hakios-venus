import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old = '''				printf("pcie: 5:   21: bar0 0x128 = 0x%08x (star wants 0)\\n", rd(bar0.base + 0x128));
'''
new = '''				printf("pcie: 5:   21: bar0 0x128 = 0x%08x (star wants 0)\\n", rd(bar0.base + 0x128));
				/*
				 * apply-220: vendor's mhi_async_power_up() refuses to run
				 * until msi_allocated >= total_ev_rings, so MSI is enabled
				 * before BHI is ever rung.  The endpoint's MSI capability
				 * lives at 0x50 in its config space (id 0x05, next 0x70,
				 * control 0x015b: enabled, 32 vectors, per-vector masking)
				 * and the message address Android programs is 0xa0000040,
				 * the GIC ITS doorbell on this phone.  We only turn the
				 * enable bit on; the address and data are left as the
				 * bootloader left them so nothing is pointed anywhere new.
				 */
				if (smmu_state == 1 && pcie_dma_extra != 0) {
					uint32_t cap = rd(conf.base + 0x50);
					uint32_t addr_low = rd(conf.base + 0x54);
					uint32_t data = rd(conf.base + 0x58);
					uint32_t mask = rd(conf.base + 0x5c);
					uint32_t enabled;

					printf("pcie: 5:   21: msi before: cap 0x%08x addr 0x%08x data 0x%08x mask 0x%08x\\n",
					       cap, addr_low, data, mask);
					wr(conf.base + 0x5c, 0u);
					wr(conf.base + 0x50, (cap & 0xffff0000u) | ((cap & 0xfffeu) | 1u));
					enabled = rd(conf.base + 0x50);
					printf("pcie: 5:   21: msi after: cap 0x%08x (enabled %u, vectors %u, mask 0x%08x)\\n",
					       enabled, enabled & 1u, (enabled >> 1) & 7u, rd(conf.base + 0x5c));
				}
'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("ok apply-220")