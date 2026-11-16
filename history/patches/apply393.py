#!/usr/bin/env python3
"""apply-393: what does the firmware think of itself?  Read-only register dump.

p433 settled the fetch question with a positive control: a TRE whose payload pointer is
0x80000000 (outside MHICTRLBASE..MHICTRLLIMIT) puts ch0 into ERROR, while the very same TRE
leaves ch20 and ch4 untouched.  So ch20 (IPCR) and ch4 (DIAG) have no client at all - the
firmware runs its MHI engine and nothing above it.

Now read what the BHI block says about the image it was given, plus the whole MHI register
window, while the device sits in EE=2.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
START = "\t/* apply-392: "

BLOCK = r'''	/* apply-393: read-only.  The MHI window and the BHI block, while EE is AMSS. */
	if (pcie_mhi_data == 16u && smmu_state == 1 && pcie_dma_extra != 0) {
		uint32_t k93;
		printf("apply-393 ee 0x%08x mh 0x%08x ctrl 0x%08x cfg 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(bar0.base + 0x38), rd(bar0.base + 0x10));
		printf("apply-393 mhi 00 0x%08x 04 0x%08x 08 0x%08x 0c 0x%08x\n",
		    rd(bar0.base + 0x00), rd(bar0.base + 0x04), rd(bar0.base + 0x08), rd(bar0.base + 0x0c));
		printf("apply-393 chdb 0x%08x erdb 0x%08x bhi 0x%08x bhie 0x%08x\n",
		    rd(bar0.base + 0x18), rd(bar0.base + 0x20), rd(bar0.base + 0x28), rd(bar0.base + 0x2c));
		printf("apply-393 lbase 0x%08x 0x%08x limit 0x%08x 0x%08x db 0x%08x ee128 0x%08x\n",
		    rd(bar0.base + 0x80), rd(bar0.base + 0x84), rd(bar0.base + 0x88), rd(bar0.base + 0x8c),
		    rd(bar0.base + 0x20), rd(bar0.base + 0x128));
		printf("apply-393 bhi ver 0x%08x/%08x imgaddr %08x/%08x imgsize 0x%08x txdb 0x%08x\n",
		    rd(bar0.base + 0x224 + 0x00u), rd(bar0.base + 0x224 + 0x04u),
		    rd(bar0.base + 0x224 + 0x08u), rd(bar0.base + 0x224 + 0x0cu),
		    rd(bar0.base + 0x224 + 0x10u), rd(bar0.base + 0x224 + 0x18u));
		printf("apply-393 bhi intvec 0x%08x execenv 0x%08x status 0x%08x errcode 0x%08x\n",
		    rd(bar0.base + 0x224 + 0x20u), rd(bar0.base + 0x224 + 0x28u),
		    rd(bar0.base + 0x224 + 0x2cu), rd(bar0.base + 0x224 + 0x30u));
		printf("apply-393 bhi errdbg %08x %08x %08x serialnu 0x%08x numseg 0x%08x\n",
		    rd(bar0.base + 0x224 + 0x34u), rd(bar0.base + 0x224 + 0x38u), rd(bar0.base + 0x224 + 0x3cu),
		    rd(bar0.base + 0x224 + 0x40u), rd(bar0.base + 0x224 + 0x48u));
		printf("apply-393 bhie txstat 0x%08x rxvec %08x/%08x/%08x/%08x\n",
		    rd(bar0.base + 0x224 + 0x44u),
		    rd(bar0.base + 0x224 + 0x60u), rd(bar0.base + 0x224 + 0x64u),
		    rd(bar0.base + 0x224 + 0x68u), rd(bar0.base + 0x224 + 0x70u));
		printf("apply-393 bhie txvec %08x/%08x size %08x db 0x%08x\n",
		    rd(bar0.base + 0x224 + 0x2cu), rd(bar0.base + 0x224 + 0x30u),
		    rd(bar0.base + 0x224 + 0x34u), rd(bar0.base + 0x224 + 0x3cu));
		/* and the same two registers a second later, to see whether anything moves */
		sleep_ms(500);
		printf("apply-393 after 500 ms: ee 0x%08x mh 0x%08x bhi status 0x%08x errcode 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48),
		    rd(bar0.base + 0x224 + 0x2cu), rd(bar0.base + 0x224 + 0x30u));
		for (k93 = 0; k93 < 4u; k93++)
			printf("apply-393 ch%u st 0x%08x eri 0x%08x rbase 0x%08x rlen 0x%08x rp 0x%08x wp 0x%08x\n",
			    (k93 == 0u) ? 0u : ((k93 == 1u) ? 1u : ((k93 == 2u) ? 20u : 21u)),
			    rd(pcie_dma_extra + ((k93 == 0u) ? 0u : ((k93 == 1u) ? 0x2cu : ((k93 == 2u) ? 20u * 0x2cu : 21u * 0x2cu)))),
			    rd(pcie_dma_extra + ((k93 == 0u) ? 0u : ((k93 == 1u) ? 0x2cu : ((k93 == 2u) ? 20u * 0x2cu : 21u * 0x2cu))) + 0x08u),
			    rd(pcie_dma_extra + ((k93 == 0u) ? 0u : ((k93 == 1u) ? 0x2cu : ((k93 == 2u) ? 20u * 0x2cu : 21u * 0x2cu))) + 0x0cu),
			    rd(pcie_dma_extra + ((k93 == 0u) ? 0u : ((k93 == 1u) ? 0x2cu : ((k93 == 2u) ? 20u * 0x2cu : 21u * 0x2cu))) + 0x14u),
			    rd(pcie_dma_extra + ((k93 == 0u) ? 0u : ((k93 == 1u) ? 0x2cu : ((k93 == 2u) ? 20u * 0x2cu : 21u * 0x2cu))) + 0x1cu),
			    rd(pcie_dma_extra + ((k93 == 0u) ? 0u : ((k93 == 1u) ? 0x2cu : ((k93 == 2u) ? 20u * 0x2cu : 21u * 0x2cu))) + 0x24u));
		printf("apply-393 done\n");
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()

assert src.count(START) == 1, "apply-392 block marker not found"
a = src.index(START)
src = src[:a] + BLOCK + src[a:]

old = "pcie_mhi_data != 12u && pcie_mhi_data != 13u && pcie_mhi_data != 14u && pcie_mhi_data != 15u"
assert src.count(old) == 2, "expected two gates, found %d" % src.count(old)
src = src.replace(old, "pcie_mhi_data != 12u && pcie_mhi_data != 13u && pcie_mhi_data != 14u && pcie_mhi_data != 15u && pcie_mhi_data != 16u")

assert src.count("apply-393 done") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-393 ok")
