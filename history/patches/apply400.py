#!/usr/bin/env python3
"""apply-400: arm BHIE RX *before* the BHI download, then force RDDM and see if a dump lands.

p438 armed BHIE RX after M0 and got nothing; the register read back as something we never
wrote, so AMSS overwrote it.  The vendor arms it in mhi_prepare_for_power_up(), i.e. before
any image is transferred, and the firmware latches the drain address while it is still SBL.
Two blocks this time: one before the bhi handshake, one after AMSS is up.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"
ANCHOR = "\t\t\t\t\twr(bar0.base + 0x108, (uint32_t)bhi_addr);\n\t\t\t\t\twr(bar0.base + 0x110, (uint32_t)bhi_size);\n"

PRE = r'''	/* apply-400: arm BHIE RX before the bhi download, the way mhi_rddm_prepare() does
	 * inside mhi_prepare_for_power_up().  SBL latches the drain address; arming it
	 * after M0 (p438) was too late and got overwritten. */
	if (pcie_mhi_data == 23u && smmu_state == 1 && pcie_dma_extra != 0) {
		uint64_t rddm_iova = PCIE_EXTRA_IOVA + 0x500000ull;
		uint32_t bhie = rd(bar0.base + 0x2c);
		uint32_t k400;

		printf("apply-400 a: bhie 0x%08x rddm iova 0x%llx ee 0x%08x mh 0x%08x\n",
		    bhie, (unsigned long long)rddm_iova, rd(bar0.base + 0x128), rd(bar0.base + 0x48));
		if (bhie != 0 && bhie < 0x1000u) {
			for (k400 = 0; k400 < 0x2000u; k400 += 4u)
				wr(pcie_dma_extra + 0x500000u + k400, 0x0badf00du);
			__asm__ __volatile__("dsb sy" ::: "memory");
			wr(bar0.base + bhie + 0x60u, (uint32_t)rddm_iova);
			wr(bar0.base + bhie + 0x64u, (uint32_t)(rddm_iova >> 32));
			wr(bar0.base + bhie + 0x68u, 0x00200000u);
			wr(bar0.base + bhie + 0x70u, 0x00005500u);
			printf("apply-400 b: rxvec %08x/%08x size 0x%08x db 0x%08x status 0x%08x\n",
			    rd(bar0.base + bhie + 0x60u), rd(bar0.base + bhie + 0x64u),
			    rd(bar0.base + bhie + 0x68u), rd(bar0.base + bhie + 0x70u),
			    rd(bar0.base + bhie + 0x78u));
		} else {
			printf("apply-400 b: bhie offset 0x%08x is not usable\n", bhie);
		}
	}

'''

POST = r'''	/* apply-400: after AMSS is up, force the soc reset, pin rddm and look for a dump. */
	if (pcie_mhi_data == 23u && smmu_state == 1 && pcie_dma_extra != 0 &&
	    rd(bar0.base + 0x128) == 2u) {
		uint32_t bhie = rd(bar0.base + 0x2c);
		uint32_t k400;

		printf("apply-400 c: pre reset rxvec %08x/%08x size 0x%08x db 0x%08x status 0x%08x\n",
		    rd(bar0.base + bhie + 0x60u), rd(bar0.base + bhie + 0x64u),
		    rd(bar0.base + bhie + 0x68u), rd(bar0.base + bhie + 0x70u),
		    rd(bar0.base + bhie + 0x78u));
		wr(bar0.base + 0xb0, 1u);
		for (k400 = 0; k400 < 20u; k400++) {
			sleep_ms(100);
			if (rd(bar0.base + 0x128) == 3u)
				break;
		}
		printf("apply-400 d: after %u ms ee 0x%08x mh 0x%08x\n", k400 * 100u,
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48));
		wr(bar0.base + 0xb0, 1u);		/* the second write pins rddm */
		sleep_ms(1500);
		printf("apply-400 e: pinned ee 0x%08x status 0x%08x rxvec %08x/%08x db 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + bhie + 0x78u),
		    rd(bar0.base + bhie + 0x60u), rd(bar0.base + bhie + 0x64u),
		    rd(bar0.base + bhie + 0x70u));
		printf("apply-400 f: buf %08x %08x %08x %08x | %08x %08x %08x %08x\n",
		    rd(pcie_dma_extra + 0x500000u), rd(pcie_dma_extra + 0x500004u),
		    rd(pcie_dma_extra + 0x500008u), rd(pcie_dma_extra + 0x50000cu),
		    rd(pcie_dma_extra + 0x500010u), rd(pcie_dma_extra + 0x500014u),
		    rd(pcie_dma_extra + 0x500018u), rd(pcie_dma_extra + 0x50001cu));
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1, "end marker"
assert src.count(ANCHOR) == 1, "bhi anchor"
assert "apply-400" not in src
count = src.count("pcie_mhi_data != 21u")
assert count == 2, "expected 2 gates with 21u, found %d" % count
src = src.replace("pcie_mhi_data != 21u", "pcie_mhi_data != 21u && pcie_mhi_data != 23u")

src = src.replace(ANCHOR, PRE + ANCHOR)
i = src.index(END)
src = src[:i] + POST + src[i:]
assert src.count("apply-400 f") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-400 ok")
