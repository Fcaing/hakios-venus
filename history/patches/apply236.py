import io, sys
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
src = open(p, encoding="utf-8", errors="replace").read()

anchor = """					printf("pcie: 5:   21: apply-232: bhi gets addr 0x%llx size 0x%llx (fw 0x%llx)\\n",
					    (unsigned long long)bhi_addr, (unsigned long long)bhi_size,
					    (unsigned long long)pcie_fw_size);
"""
assert src.count(anchor) == 1, ("anchor count", src.count(anchor))

block = anchor + """					/*
					 * apply-236: star's stage 16 guard probe.  Ring the
					 * doorbell with an address that no SMMU mapping covers
					 * and look for the translation fault.  A fault whose FAR
					 * equals the guard proves the endpoint reads through the
					 * owned context (SID 0x1c01); no fault at all means it
					 * walks host physical addresses and every \"success\" so
					 * far read whatever happened to live at that address.
					 */
					{
						uint32_t guard_on = 0, guard_addr = 0;

						if (PE_parse_boot_argn("pcie_guard", &guard_on, sizeof(guard_on)) && guard_on != 0) {
							uint64_t gaddr = 0xa0100000ull;
							uint32_t k, fsr = 0, global = 0, sid = 0;
							uint64_t far = 0;

							if (PE_parse_boot_argn("pcie_guard_addr", &guard_addr, sizeof(guard_addr)) && guard_addr != 0) {
								gaddr = guard_addr;
							}
							wr(smmu_cb + 0x58, 0xffffffff);
							wr(smmu_mmio + 0x48, 0xffffffff);
							wr(bar0.base + 0x12c, 0);
							wr(bar0.base + 0x10c, (uint32_t)(gaddr >> 32));
							wr(bar0.base + 0x108, (uint32_t)gaddr);
							wr(bar0.base + 0x110, 4096);
							wr(bar0.base + 0x118, 1);
							for (k = 0; k < 200; k++) {
								fsr = rd(smmu_cb + 0x58);
								global = rd(smmu_mmio + 0x48);
								if ((fsr & 2u) != 0 || global != 0) {
									break;
								}
								sleep_ms(5);
							}
							far = ((uint64_t)rd(smmu_cb + 0x64) << 32) | (uint64_t)rd(smmu_cb + 0x60);
							sid = rd(smmu_mmio + 0x1400 + 4 * smmu_context) & 0xffffu;
							printf("pcie: 5:   21: apply-236 guard 0x%llx after %u: fsr 0x%08x far 0x%llx sid 0x%04x gfsr 0x%08x bhi 0x%08x ee 0x%08x\\n",
							    (unsigned long long)gaddr, k, fsr, (unsigned long long)far, sid,
							    global, rd(bar0.base + 0x12c), rd(bar0.base + 0x128));
							wr(smmu_cb + 0x58, 0xffffffff);
							wr(smmu_mmio + 0x48, 0xffffffff);
							wr(bar0.base + 0x12c, 0);
						}
					}
"""

src = src.replace(anchor, block, 1)
open(p, "w", encoding="utf-8").write(src)
print("patched, %d -> %d bytes" % (len(anchor), len(block)))