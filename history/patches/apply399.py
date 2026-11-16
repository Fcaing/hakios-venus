#!/usr/bin/env python3
"""apply-399: read the BHI block where it actually lives.

The star port (ref: lemonade_wifi.c:770-790) polls BHI_STATUS at bar+0x12c and the error
code at bar+0x130 -- i.e. BHIOFF (read from 0x28, 0x100 here) + 0x2c/0x30 -- and requires
(status >> 30) == 2 with EE == 1 before it will believe the prefix landed.  Every round of
ours has been reading 0x224+0x2c instead, which is the BHIE block, so the BHI verdict has
never actually been checked.  Read the whole 0x100 block and say what it holds.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-399: the BHI block at BHIOFF, not at the BHIE base. */
	if (pcie_mhi_data == 22u && smmu_state == 1 && pcie_dma_extra != 0) {
		uint32_t bhi399 = rd(bar0.base + 0x28);
		uint32_t bhie399 = rd(bar0.base + 0x2c);
		printf("apply-399 a: bhi off 0x%08x bhie off 0x%08x ee 0x%08x mh 0x%08x\n",
		    bhi399, bhie399, rd(bar0.base + 0x128), rd(bar0.base + 0x48));
		printf("apply-399 b: bhi ver %08x/%08x imgaddr %08x/%08x imgsize 0x%08x txdb 0x%08x\n",
		    rd(bar0.base + bhi399 + 0x00u), rd(bar0.base + bhi399 + 0x04u),
		    rd(bar0.base + bhi399 + 0x08u), rd(bar0.base + bhi399 + 0x0cu),
		    rd(bar0.base + bhi399 + 0x10u), rd(bar0.base + bhi399 + 0x18u));
		printf("apply-399 c: bhi intvec 0x%08x execenv 0x%08x status 0x%08x errcode 0x%08x\n",
		    rd(bar0.base + bhi399 + 0x20u), rd(bar0.base + bhi399 + 0x28u),
		    rd(bar0.base + bhi399 + 0x2cu), rd(bar0.base + bhi399 + 0x30u));
		printf("apply-399 d: bhi errdbg %08x %08x %08x serial 0x%08x numseg 0x%08x\n",
		    rd(bar0.base + bhi399 + 0x34u), rd(bar0.base + bhi399 + 0x38u),
		    rd(bar0.base + bhi399 + 0x3cu), rd(bar0.base + bhi399 + 0x40u),
		    rd(bar0.base + bhi399 + 0x48u));
		printf("apply-399 e: bhie txstat 0x%08x txvec %08x/%08x size 0x%08x db 0x%08x\n",
		    rd(bar0.base + bhie399 + 0x44u),
		    rd(bar0.base + bhie399 + 0x2cu), rd(bar0.base + bhie399 + 0x30u),
		    rd(bar0.base + bhie399 + 0x34u), rd(bar0.base + bhie399 + 0x3cu));
		sleep_ms(50);
		printf("apply-399 f: after 50 ms status 0x%08x errcode 0x%08x ee 0x%08x\n",
		    rd(bar0.base + bhi399 + 0x2cu), rd(bar0.base + bhi399 + 0x30u),
		    rd(bar0.base + 0x128));
		/* and the two data channels while we are here */
		printf("apply-399 g: ch20 st 0x%08x eri %u rbase 0x%08x rp 0x%08x wp 0x%08x\n",
		    rd(pcie_dma_extra + 20u * 0x2cu), rd(pcie_dma_extra + 20u * 0x2cu + 0x08u),
		    rd(pcie_dma_extra + 20u * 0x2cu + 0x0cu), rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu),
		    rd(pcie_dma_extra + 20u * 0x2cu + 0x24u));
		printf("apply-399 h: ch21 st 0x%08x eri %u rbase 0x%08x rp 0x%08x wp 0x%08x\n",
		    rd(pcie_dma_extra + 21u * 0x2cu), rd(pcie_dma_extra + 21u * 0x2cu + 0x08u),
		    rd(pcie_dma_extra + 21u * 0x2cu + 0x0cu), rd(pcie_dma_extra + 21u * 0x2cu + 0x1cu),
		    rd(pcie_dma_extra + 21u * 0x2cu + 0x24u));
		printf("apply-399 done\n");
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1 and "apply-399" not in src

old_gate = "pcie_mhi_data != 17u && pcie_mhi_data != 21u && pcie_chanstart != 0"
assert src.count(old_gate) == 1
src = src.replace(old_gate, "pcie_mhi_data != 17u && pcie_mhi_data != 21u && pcie_mhi_data != 22u && pcie_chanstart != 0")

old_gate2 = "pcie_mhi_data != 17u && pcie_mhi_data != 21u) wr(pcie_dma_extra + 20 * 0x2c"
assert src.count(old_gate2) == 1
src = src.replace(old_gate2, "pcie_mhi_data != 17u && pcie_mhi_data != 21u && pcie_mhi_data != 22u) wr(pcie_dma_extra + 20 * 0x2c")

a = src.index(END)
src = src[:a] + BLOCK + src[a:]
assert src.count("apply-399 done") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-399 ok")
