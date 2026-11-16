#!/usr/bin/env python3
"""apply-404: do what star's ipcr_probe() does, step for step.

The star port (lemonade_wifi.c:1230) does more than we ever did:
  - rewrite both channel contexts,
  - START_CHAN(20) *and* START_CHAN(21),
  - fill 32 RX TREs on ch21 and set its wp to the 31st element,
  - ring ch21's doorbell,
  - then send a QRTR HELLO on ch20 (src port 0xfffffffe -> node 0xffffffff port 0xfffffffe,
    payload {command=2, words[4]=0}), and wait for the firmware to answer.

We only ever did START_CHAN(20), never touched ch21's doorbell, and never sent a HELLO.
This round does the whole sequence and prints whatever comes back.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-404: the full IPCR bring-up, the way star does it. */
	if (pcie_mhi_data == 25u && smmu_state == 1 && pcie_dma_extra != 0 &&
	    rd(bar0.base + 0x128) == 2u) {
		uint32_t k404, st, base20, wp20, base21, i;
		uint32_t txiova = (uint32_t)(PCIE_EXTRA_IOVA + 0x410000u);
		vm_offset_t txbuf = pcie_dma_extra + 0x410000u;
		uint32_t rxiova = (uint32_t)(PCIE_EXTRA_IOVA + 0x300000u);
		uint32_t *pkt;
		uint32_t code20 = 0, code21 = 0, seen;

		printf("apply-404 a: ee 0x%08x mh 0x%08x ch20 0x%08x ch21 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48),
		    rd(pcie_dma_extra + 20u * 0x2cu), rd(pcie_dma_extra + 21u * 0x2cu));

		/* 1. rewrite both contexts exactly as star does */
		for (k404 = 20; k404 <= 21; k404++) {
			vm_offset_t c = pcie_dma_extra + k404 * 0x2cu;
			uint32_t rb = (uint32_t)(PCIE_EXTRA_IOVA + 0x8000u + (k404 - 20u) * 0x1000u);
			wr(c + 0x00u, 1u | (2u << 8));
			wr(c + 0x04u, (k404 == 20u) ? 1u : 2u);
			wr(c + 0x08u, 1u);
			wr(c + 0x0cu, rb); wr(c + 0x10u, 0u);
			wr(c + 0x14u, 32u * 16u);
			wr(c + 0x1cu, rb); wr(c + 0x20u, 0u);
			wr(c + 0x24u, rb); wr(c + 0x28u, 0u);
		}
		__asm__ __volatile__("dsb sy" ::: "memory");
		printf("apply-404 b: ch20 0x%08x rbase 0x%08x len 0x%08x | ch21 0x%08x rbase 0x%08x\n",
		    rd(pcie_dma_extra + 20u * 0x2cu), rd(pcie_dma_extra + 20u * 0x2cu + 0x0cu),
		    rd(pcie_dma_extra + 20u * 0x2cu + 0x14u),
		    rd(pcie_dma_extra + 21u * 0x2cu), rd(pcie_dma_extra + 21u * 0x2cu + 0x0cu));

		/* 2. START_CHAN(20) then START_CHAN(21) through the command ring */
		{
			uint32_t cmdwp = rd(pcie_dma_extra + 0x2424u);
			uint32_t cmdiova = cmdwp;
			vm_offset_t cmdt = pcie_dma_extra + (cmdiova - (uint32_t)PCIE_EXTRA_IOVA);

			for (k404 = 0; k404 < 2u; k404++) {
				uint32_t ch = 20u + k404;
				wr(cmdt + 0x00u, 0u); wr(cmdt + 0x04u, 0u);
				wr(cmdt + 0x08u, 0u);
				wr(cmdt + 0x0cu, (ch << 24) | (0x12u << 16));
				__asm__ __volatile__("dc civac, %0" :: "r"(cmdt) : "memory");
				__asm__ __volatile__("dsb sy" ::: "memory");
				cmdwp += 16u;
				wr(pcie_dma_extra + 0x2424u, cmdwp);
				wr(bar0.base + 0x74u, 0u);
				wr(bar0.base + 0x70u, cmdwp);
				for (i = 0; i < 60u; i++) {
					sleep_ms(5);
					seen = rd(pcie_dma_extra + 0x2000u + 0x1cu);
					if (seen != rd(pcie_dma_extra + 0x2000u + 0x1cu)) {
						break;
					}
				}
				printf("apply-404 c: START_CHAN(%u) sent, cmd wp 0x%08x er0 slots %08x %08x %08x\n",
				    ch, cmdwp,
				    rd(pcie_dma_extra + 0x2000u + 0x30u), rd(pcie_dma_extra + 0x2000u + 0x40u),
				    rd(pcie_dma_extra + 0x2000u + 0x50u));
			}
			/* read the two completions straight out of er0, wherever they landed */
			for (i = 0; i < 8u; i++) {
				vm_offset_t e = pcie_dma_extra + 0x2000u + i * 16u;
				uint32_t d2 = rd(e + 0x08u), d3 = rd(e + 0x0cu);
				if (((d3 >> 16) & 0xffu) == 0x21u) {
					printf("apply-404 d: er0[%u] completion code %u ch %u\n",
					    i, (d2 >> 16) & 0xffu, d3 & 0xffu);
					if ((d3 & 0xffu) == 20u) code20 = (d2 >> 16) & 0xffu;
					if ((d3 & 0xffu) == 21u) code21 = (d2 >> 16) & 0xffu;
				}
			}
			printf("apply-404 e: completion codes 20=%u 21=%u\n", code20, code21);
		}

		/* 3. ch21: 32 RX TREs, wp at the 31st element, ring the doorbell */
		base21 = (uint32_t)(PCIE_EXTRA_IOVA + 0x9000u);
		for (i = 0; i < 32u; i++) {
			vm_offset_t t = pcie_dma_extra + 0x9000u + i * 16u;
			wr(t + 0x00u, rxiova + i * 0x8000u);
			wr(t + 0x04u, 0u);
			wr(t + 0x08u, 0x00008000u);
			wr(t + 0x0cu, 0x00020200u);
		}
		__asm__ __volatile__("dsb sy" ::: "memory");
		wr(pcie_dma_extra + 21u * 0x2cu + 0x24u, base21 + 31u * 16u);
		wr(pcie_dma_extra + 21u * 0x2cu + 0x28u, 0u);
		__asm__ __volatile__("dsb sy" ::: "memory");
		wr(bar0.base + 0x300u + 21u * 8u + 4u, 0u);
		wr(bar0.base + 0x300u + 21u * 8u, base21 + 31u * 16u);
		printf("apply-404 f: ch21 wp 0x%08x rung at 0x%08x\n",
		    base21 + 31u * 16u, rd(bar0.base + 0x300u + 21u * 8u));

		/* 4. QRTR HELLO on ch20 */
		pkt = (uint32_t *)(void *)txbuf;
		for (i = 0; i < 32u; i++)
			pkt[i] = 0u;
		pkt[0] = 1u;			/* version */
		pkt[1] = 2u;			/* QRTR_TYPE_HELLO */
		pkt[2] = 1u;			/* source node */
		pkt[3] = 0xfffffffeu;		/* source port = control */
		pkt[4] = 0u;			/* confirm */
		pkt[5] = 20u;			/* payload size */
		pkt[6] = 0xffffffffu;		/* dest node = broadcast */
		pkt[7] = 0xfffffffeu;		/* dest port = control */
		pkt[8] = 2u;			/* command = hello */
		pkt[9] = 0u; pkt[10] = 0u; pkt[11] = 0u; pkt[12] = 0u;
		for (i = 0; i < 128u; i += 64) {
			__asm__ __volatile__("dc civac, %0" :: "r"(txbuf + (vm_offset_t)i) : "memory");
		}
		__asm__ __volatile__("dsb sy" ::: "memory");

		base20 = (uint32_t)(PCIE_EXTRA_IOVA + 0x8000u);
		wp20 = rd(pcie_dma_extra + 20u * 0x2cu + 0x24u);
		if (wp20 < base20 || wp20 > base20 + 31u * 16u)
			wp20 = base20;
		{
			vm_offset_t t = pcie_dma_extra + (wp20 - (uint32_t)PCIE_EXTRA_IOVA);
			wr(t + 0x00u, txiova);
			wr(t + 0x04u, 0u);
			wr(t + 0x08u, 52u);
			wr(t + 0x0cu, 0x00020200u);
			__asm__ __volatile__("dc civac, %0" :: "r"(t) : "memory");
			__asm__ __volatile__("dsb sy" ::: "memory");
			wp20 += 16u;
			wr(pcie_dma_extra + 20u * 0x2cu + 0x24u, wp20);
			__asm__ __volatile__("dsb sy" ::: "memory");
			wr(bar0.base + 0x300u + 20u * 8u + 4u, 0u);
			wr(bar0.base + 0x300u + 20u * 8u, wp20);
			printf("apply-404 g: hello queued at 0x%08x, ch20 wp 0x%08x rung\n", txiova, wp20);
		}

		/* 5. watch for two seconds: any event, any RX on ch21 */
		st = rd(pcie_dma_extra + 21u * 0x2cu);
		for (i = 0; i < 400u; i++) {
			sleep_ms(5);
			if (rd(pcie_dma_extra + 21u * 0x2cu) != st ||
			    rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu) != rd(pcie_dma_extra + 20u * 0x2cu + 0x24u)) {
				printf("apply-404 h: t=%u ms ch20 st 0x%08x rp 0x%08x wp 0x%08x ch21 st 0x%08x rp 0x%08x wp 0x%08x\n",
				    i * 5u, rd(pcie_dma_extra + 20u * 0x2cu),
				    rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu), rd(pcie_dma_extra + 20u * 0x2cu + 0x24u),
				    rd(pcie_dma_extra + 21u * 0x2cu),
				    rd(pcie_dma_extra + 21u * 0x2cu + 0x1cu), rd(pcie_dma_extra + 21u * 0x2cu + 0x24u));
			}
		}
		printf("apply-404 i: end ee 0x%08x ch20 0x%08x rp 0x%08x wp 0x%08x ch21 0x%08x rp 0x%08x\n",
		    rd(bar0.base + 0x128), rd(pcie_dma_extra + 20u * 0x2cu),
		    rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu), rd(pcie_dma_extra + 20u * 0x2cu + 0x24u),
		    rd(pcie_dma_extra + 21u * 0x2cu), rd(pcie_dma_extra + 21u * 0x2cu + 0x1cu));
		for (i = 0; i < 8u; i++) {
			vm_offset_t e = pcie_dma_extra + 0x2000u + i * 16u;
			printf("apply-404 j: er0[%u] %08x %08x %08x %08x\n", i,
			    rd(e), rd(e + 4), rd(e + 8), rd(e + 12));
		}
		for (i = 0; i < 4u; i++) {
			vm_offset_t e = pcie_dma_extra + 0x2000u + 0x2cu + i * 16u;
			printf("apply-404 k: er1[%u] %08x %08x %08x %08x\n", i,
			    rd(e), rd(e + 4), rd(e + 8), rd(e + 12));
		}
		printf("apply-404 l: rx buf %08x %08x %08x %08x / %08x %08x\n",
		    rd(pcie_dma_extra + 0x300000u), rd(pcie_dma_extra + 0x300004u),
		    rd(pcie_dma_extra + 0x300008u), rd(pcie_dma_extra + 0x30000cu),
		    rd(pcie_dma_extra + 0x310000u), rd(pcie_dma_extra + 0x310004u));
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1
assert "apply-404" not in src

a1 = "pcie_mhi_data != 24u && pcie_chanstart != 0"
a2 = "pcie_mhi_data != 24u) wr(pcie_dma_extra + 20 * 0x2c"
assert src.count(a1) == 1 and src.count(a2) == 1, (src.count(a1), src.count(a2))
src = src.replace(a1, "pcie_mhi_data != 24u && pcie_mhi_data != 25u && pcie_chanstart != 0")
src = src.replace(a2, "pcie_mhi_data != 24u && pcie_mhi_data != 25u) wr(pcie_dma_extra + 20 * 0x2c")

a = src.index(END)
src = src[:a] + BLOCK + src[a:]
assert src.count("apply-404 l") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-404 ok")
