import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old = '''				printf("pcie: 5:   21: bar0 0x128 = 0x%08x (star wants 0)\\n", rd(bar0.base + 0x128));
'''
new = '''				printf("pcie: 5:   21: bar0 0x128 = 0x%08x (star wants 0)\\n", rd(bar0.base + 0x128));
				/*
				 * apply-219: the PBL hands the endpoint over to MHI once it
				 * has the SBL, and MHI needs a context base, an event ring
				 * and a command ring before the firmware can report READY.
				 * star programs exactly these three addresses (and the two
				 * window bases) in its mhi_prepare() before it rings the
				 * doorbell, and its MHISTATUS.READY does come up.  Ours were
				 * never written, so the PBL had nowhere to deliver the
				 * session and stopped after the image.
				 */
				if (smmu_state == 1 && pcie_dma_extra != 0) {
					uint64_t ctxt = (uint64_t)PCIE_EXTRA_IOVA;
					uint64_t ering = ctxt + 0x800;
					uint64_t cring = ctxt + 0xc00;
					uint32_t cfg = rd(bar0.base + 0x10);

					wr(bar0.base + 0x58, (uint32_t)ctxt);
					wr(bar0.base + 0x5c, (uint32_t)(ctxt >> 32));
					wr(bar0.base + 0x60, (uint32_t)ering);
					wr(bar0.base + 0x64, (uint32_t)(ering >> 32));
					wr(bar0.base + 0x68, (uint32_t)cring);
					wr(bar0.base + 0x6c, (uint32_t)(cring >> 32));
					wr(bar0.base + 0x10, (cfg & 0xffffu) | (3u << 16));
					wr(bar0.base + 0x80, (uint32_t)ctxt);
					wr(bar0.base + 0x84, (uint32_t)(ctxt >> 32));
					wr(bar0.base + 0x88, 0xb0000000u);
					wr(bar0.base + 0x8c, 0u);
					wr(bar0.base + 0x98, (uint32_t)ctxt);
					wr(bar0.base + 0x9c, (uint32_t)(ctxt >> 32));
					wr(bar0.base + 0xa0, 0xb0000000u);
					wr(bar0.base + 0xa4, 0u);
					printf("pcie: 5:   21: mhi ctxt 0x%llx er 0x%llx cmd 0x%llx, cfg 0x%08x -> 0x%08x\\n",
					       ctxt, ering, cring, cfg, rd(bar0.base + 0x10));
					printf("pcie: 5:   21: mhi readback 0x58 %08x:%08x 0x60 %08x:%08x 0x68 %08x:%08x\\n",
					       rd(bar0.base + 0x5c), rd(bar0.base + 0x58),
					       rd(bar0.base + 0x64), rd(bar0.base + 0x60),
					       rd(bar0.base + 0x6c), rd(bar0.base + 0x68));
				}
'''
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("ok apply-219")