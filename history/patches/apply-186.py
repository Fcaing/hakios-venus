import io

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old = """					printf("pcie: 5:   21: bhi id: ver 0x%08x maj 0x%08x serial 0x%08x anti 0x%08x segs 0x%08x hwid 0x%08x ivec 0x%08x\\n",
					       ver, maj, serial, anti, segs, hwid, ivec);
				}"""
new = """					printf("pcie: 5:   21: bhi id: ver 0x%08x maj 0x%08x serial 0x%08x anti 0x%08x segs 0x%08x hwid 0x%08x ivec 0x%08x\\n",
					       ver, maj, serial, anti, segs, hwid, ivec);
					(void)ivec;
				}
				/*
				 * apply-186: mhi_prepare_for_bhi() writes BHI_INTVEC = 0
				 * before it touches the doorbell.  Ours still reads
				 * 0xffffffff, which no firmware can report to.
				 */
				wr(bar0.base + 0x120, 0);
				printf("pcie: 5:   21: bhie off 0x%08x, intvec now 0x%08x\\n",
				       rd(bar0.base + 0x2c), rd(bar0.base + 0x120));"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

io.open(p, "w", encoding="utf-8").write(s)
print("patched")