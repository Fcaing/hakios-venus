#!/usr/bin/env python3
"""apply-385: catch RDDM, read the BHI window while we are there, and try to keep it.

p418 showed that writing 1 to 0xb0 walks EE 2 -> 3 (RDDM) within ~9 ms, and that the
device is back on AMSS about half a second later.  If RDDM still honours the BHI image
registers we can replay BHI -> BHIE -> AMSS inside one boot and cut a round from five
minutes to seconds, which is the whole schedule lever for the QMI work.  So:

  1. read the starting state (ee, mh, ch20/ch21 contexts and ring heads, ER0);
  2. write 0xb0 = 1, poll every millisecond for a second and print the BHI window
     (IMGSIZE / IMGTXDB / EXECENV / STATUS / ERRCODE / MSMSOCID) at every EE change;
  3. the first time EE reads 3, write 0xb0 = 1 again - does RDDM stick?
  4. report where we ended up, and whether ch21 (device -> host) ever produced a TRE.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
MARK = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-385: catch RDDM, read the BHI window, try to pin it there. */
	if (pcie_mhi_data == 8u && smmu_state == 1 && pcie_dma_extra != 0) {
		uint32_t c20 = 20u * 0x2cu, c21 = 21u * 0x2cu, t85, ee85, last85, pin85 = 0;
		printf("apply-385 t0: ee 0x%08x mh 0x%08x ctrl 0x%08x cfg 0x%08x b0 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(bar0.base + 0x38),
		    rd(bar0.base + 0x10), rd(bar0.base + 0xb0));
		printf("apply-385 ch20: st 0x%08x type 0x%08x eri 0x%08x rbase 0x%08x len 0x%08x rp 0x%08x wp 0x%08x\n",
		    rd(pcie_dma_extra + c20), rd(pcie_dma_extra + c20 + 0x04u), rd(pcie_dma_extra + c20 + 0x08u),
		    rd(pcie_dma_extra + c20 + 0x0cu), rd(pcie_dma_extra + c20 + 0x14u),
		    rd(pcie_dma_extra + c20 + 0x1cu), rd(pcie_dma_extra + c20 + 0x24u));
		printf("apply-385 ch21: st 0x%08x type 0x%08x eri 0x%08x rbase 0x%08x len 0x%08x rp 0x%08x wp 0x%08x\n",
		    rd(pcie_dma_extra + c21), rd(pcie_dma_extra + c21 + 0x04u), rd(pcie_dma_extra + c21 + 0x08u),
		    rd(pcie_dma_extra + c21 + 0x0cu), rd(pcie_dma_extra + c21 + 0x14u),
		    rd(pcie_dma_extra + c21 + 0x1cu), rd(pcie_dma_extra + c21 + 0x24u));
		printf("apply-385 rx21 head: %08x %08x %08x %08x\n",
		    rd(pcie_dma_extra + 0xd000u), rd(pcie_dma_extra + 0xd000u + 4u),
		    rd(pcie_dma_extra + 0xd000u + 8u), rd(pcie_dma_extra + 0xd000u + 12u));
		last85 = rd(bar0.base + 0x128);
		wr(bar0.base + 0xb0, 1u);
		printf("apply-385 b0 written, ee 0x%08x\n", last85);
		for (t85 = 0; t85 < 1000u; t85++) {
			sleep_ms(1);
			ee85 = rd(bar0.base + 0x128);
			if (ee85 == last85) {
				continue;
			}
			last85 = ee85;
			printf("apply-385 t=%u ms: ee 0x%08x mh 0x%08x\n", t85, ee85, rd(bar0.base + 0x48));
			printf("apply-385 bhi: size 0x%08x txdb 0x%08x env 0x%08x st 0x%08x err 0x%08x socid 0x%08x\n",
			    rd(bar0.base + 0x224u + 0x10u), rd(bar0.base + 0x224u + 0x18u),
			    rd(bar0.base + 0x224u + 0x28u), rd(bar0.base + 0x224u + 0x2cu),
			    rd(bar0.base + 0x224u + 0x30u), rd(bar0.base + 0x224u));
			if (ee85 == 3u && pin85 == 0) {
				pin85 = 1u;
				wr(bar0.base + 0xb0, 1u);
				printf("apply-385 pinned: b0 0x%08x ee 0x%08x\n",
				    rd(bar0.base + 0xb0), rd(bar0.base + 0x128));
			}
		}
		printf("apply-385 end: ee 0x%08x mh 0x%08x b0 0x%08x ch20 st 0x%08x ch21 st 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(bar0.base + 0xb0),
		    rd(pcie_dma_extra + c20), rd(pcie_dma_extra + c21));
		printf("apply-385 rx21 after: %08x %08x %08x %08x\n",
		    rd(pcie_dma_extra + 0xd000u), rd(pcie_dma_extra + 0xd000u + 4u),
		    rd(pcie_dma_extra + 0xd000u + 8u), rd(pcie_dma_extra + 0xd000u + 12u));
		printf("apply-385 er0[0] %08x %08x %08x %08x\n", rd(pcie_dma_extra + 0x4000u),
		    rd(pcie_dma_extra + 0x4004u), rd(pcie_dma_extra + 0x4008u), rd(pcie_dma_extra + 0x400cu));
		printf("apply-385 er0[1] %08x %08x %08x %08x\n", rd(pcie_dma_extra + 0x4010u),
		    rd(pcie_dma_extra + 0x4014u), rd(pcie_dma_extra + 0x4018u), rd(pcie_dma_extra + 0x401cu));
		printf("apply-385 er0[6] %08x %08x %08x %08x\n", rd(pcie_dma_extra + 0x4060u),
		    rd(pcie_dma_extra + 0x4064u), rd(pcie_dma_extra + 0x4068u), rd(pcie_dma_extra + 0x406cu));
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()

old = "pcie_mhi_data != 4u && pcie_mhi_data != 5u && pcie_mhi_data != 6u && pcie_mhi_data != 7u"
new = old + " && pcie_mhi_data != 8u"
assert src.count(old) == 2, "expected the two ordering gates, found %d" % src.count(old)
src = src.replace(old, new)

assert src.count(MARK) == 1, "the apply-169 marker is not unique"
assert "apply-385" not in src, "apply-385 is already in the source"
src = src.replace(MARK, BLOCK + MARK)

io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-385 ok")
