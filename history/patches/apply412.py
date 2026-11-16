#!/usr/bin/env python3
"""apply-412: is the firmware just slow?  Watch the IPCR channels for ten seconds.

Everything else is ruled out, and the one thing we never did is simply wait: our longest
observation after EE=2 was two seconds, and a QCA6490 running its full AMSS + WLAN service
stack can easily take several seconds to register its MHI channels.

Read-only: poll every 100 ms for 10 s and print only when something moves (er1 rp/wp,
ch20/ch21 state+wp, EE, MHISTATUS).  If the IPCR client comes up late, ch20/ch21 will go
RUNNING or SUSPENDED and er1 will get a TRE.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-412: ten seconds of patience, watching the two IPCR channels. */
	if (pcie_mhi_data == 32u && smmu_state == 1 && pcie_dma_extra != 0) {
		uint32_t i412, ee412, mh412, s20, s21;
		uint32_t e1rp, e1wp, w20, w21;
		uint32_t p_ee, p_mh, p_s20, p_s21, p_e1rp, p_e1wp, p_w20, p_w21;

		ee412 = rd(bar0.base + 0x128);
		mh412 = rd(bar0.base + 0x48);
		s20 = rd(pcie_dma_extra + 20u * 0x2cu);
		s21 = rd(pcie_dma_extra + 21u * 0x2cu);
		e1rp = rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x1cu);
		e1wp = rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x24u);
		w20 = rd(pcie_dma_extra + 20u * 0x2cu + 0x24u);
		w21 = rd(pcie_dma_extra + 21u * 0x2cu + 0x24u);
		printf("apply-412 t0: ee 0x%08x mh 0x%08x ch20 0x%08x ch21 0x%08x er1 rp 0x%08x wp 0x%08x"
		    " wp20 0x%08x wp21 0x%08x\n", ee412, mh412, s20, s21, e1rp, e1wp, w20, w21);
		p_ee = ee412; p_mh = mh412; p_s20 = s20; p_s21 = s21;
		p_e1rp = e1rp; p_e1wp = e1wp; p_w20 = w20; p_w21 = w21;
		for (i412 = 0; i412 < 100u; i412++) {
			sleep_ms(100);
			ee412 = rd(bar0.base + 0x128);
			mh412 = rd(bar0.base + 0x48);
			s20 = rd(pcie_dma_extra + 20u * 0x2cu);
			s21 = rd(pcie_dma_extra + 21u * 0x2cu);
			e1rp = rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x1cu);
			e1wp = rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x24u);
			w20 = rd(pcie_dma_extra + 20u * 0x2cu + 0x24u);
			w21 = rd(pcie_dma_extra + 21u * 0x2cu + 0x24u);
			if (ee412 != p_ee || mh412 != p_mh || s20 != p_s20 || s21 != p_s21 ||
			    e1rp != p_e1rp || e1wp != p_e1wp || w20 != p_w20 || w21 != p_w21) {
				printf("apply-412 t=%u ms: ee 0x%08x mh 0x%08x ch20 0x%08x ch21 0x%08x"
				    " er1 rp 0x%08x wp 0x%08x wp20 0x%08x wp21 0x%08x\n",
				    i412 * 100u + 100u, ee412, mh412, s20, s21, e1rp, e1wp, w20, w21);
				p_ee = ee412; p_mh = mh412; p_s20 = s20; p_s21 = s21;
				p_e1rp = e1rp; p_e1wp = e1wp; p_w20 = w20; p_w21 = w21;
			}
		}
		printf("apply-412 end: ee 0x%08x mh 0x%08x ch20 0x%08x ch21 0x%08x er1 rp 0x%08x wp 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(pcie_dma_extra + 20u * 0x2cu),
		    rd(pcie_dma_extra + 21u * 0x2cu),
		    rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x1cu), rd(pcie_dma_extra + 0x2000u + 0x2cu + 0x24u));
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1
assert "apply-412" not in src

a = "pcie_mhi_data != 30u && pcie_chanstart != 0"
assert src.count(a) == 1, "gate A %d" % src.count(a)
src = src.replace(a, "pcie_mhi_data != 30u && pcie_mhi_data != 32u && pcie_chanstart != 0")
b = "pcie_mhi_data != 30u) wr(pcie_dma_extra + 20 * 0x2c"
assert src.count(b) == 1, "gate B %d" % src.count(b)
src = src.replace(b, "pcie_mhi_data != 30u && pcie_mhi_data != 32u) wr(pcie_dma_extra + 20 * 0x2c")

i = src.index(END)
src = src[:i] + BLOCK + src[i:]
assert src.count("apply-412 end:") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-412 ok")
