#!/usr/bin/env python3
"""apply-415: send the one command the vendor sends after mission mode and we never did.

`mhi_pm_mission_mode_transition()` ends with `mhi_init_sfr()`, and `mhi_init_sfr()`
(`mhi_init.c:834`) does three things: allocate a buffer, `mhi_send_cmd(NULL, MHI_CMD_SFR_CFG)`,
then *wait for the completion with CCS == SUCCESS*.  We have only ever sent START_CHAN.
The SFR command is (mhi_main.c:1779):
    cmd_tre->ptr      = sfr dma address
    cmd_tre->dword[0] = length
    cmd_tre->dword[1] = MHI_CMD_TYPE_SFR_CFG << 16     (73 << 16)
If the firmware is waiting for this before it brings its services up, this is the key.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-415: the SFR_CFG command the vendor sends right after mission mode. */
	if (pcie_mhi_data == 35u && smmu_state == 1 && pcie_dma_extra != 0 &&
	    rd(bar0.base + 0x128) == 2u) {
		uint32_t cofs415 = 0x2400u;			/* command context */
		uint32_t rbase415 = rd(pcie_dma_extra + cofs415 + 0x0cu);
		uint32_t rp415 = rd(pcie_dma_extra + cofs415 + 0x1cu);
		uint32_t wp415 = rd(pcie_dma_extra + cofs415 + 0x24u);
		uint64_t sfr415 = PCIE_EXTRA_IOVA + 0x200000ull;
		uint32_t soff415 = (uint32_t)(sfr415 - PCIE_EXTRA_IOVA);
		vm_offset_t sbuf415 = pcie_dma_extra + soff415;
		vm_offset_t tre415;
		uint32_t off415, i415, seen415 = 0xffffffffu, k415;

		printf("apply-415 a: cmd rbase 0x%08x rp 0x%08x wp 0x%08x sfr iova 0x%llx\n",
		    rbase415, rp415, wp415, (unsigned long long)sfr415);

		/* a clean, zeroed buffer for whatever the firmware wants to write there */
		for (k415 = 0; k415 < 0x1000u; k415 += 4u)
			wr(sbuf415 + k415, 0u);
		__asm__ __volatile__("dsb sy" ::: "memory");
		__asm__ __volatile__("dc civac, %0" :: "r"(sbuf415) : "memory");

		off415 = wp415 - rbase415;
		tre415 = pcie_dma_extra + (rbase415 - (uint32_t)PCIE_EXTRA_IOVA) + off415;
		wr(tre415 + 0x00u, (uint32_t)sfr415);
		wr(tre415 + 0x04u, (uint32_t)(sfr415 >> 32));
		wr(tre415 + 0x08u, 0x00001000u);		/* length */
		wr(tre415 + 0x0cu, 0x00490000u);		/* 73 << 16 = SFR_CFG */
		__asm__ __volatile__("dc civac, %0" :: "r"(tre415) : "memory");
		__asm__ __volatile__("dsb sy" ::: "memory");
		wr(pcie_dma_extra + cofs415 + 0x24u, wp415 + 0x10u);
		wr(bar0.base + 0x74u, 0u);
		wr(bar0.base + 0x70u, wp415 + 0x10u);
		printf("apply-415 b: sfr tre at 0x%llx (%08x %08x %08x %08x), rung 0x70 <- 0x%08x\n",
		    (unsigned long long)tre415, rd(tre415), rd(tre415 + 4u), rd(tre415 + 8u),
		    rd(tre415 + 0xcu), wp415 + 0x10u);

		/* look for the completion: type 0x21 with ptr == our buffer */
		for (i415 = 0; i415 < 100u; i415++) {
			sleep_ms(5);
			for (k415 = 0; k415 < 32u; k415++) {
				vm_offset_t e = pcie_dma_extra + 0x4000u + k415 * 16u;
				if (((rd(e + 0x0cu) >> 16) & 0xffu) == 0x21u &&
				    rd(e + 0x00u) == (uint32_t)sfr415) {
					seen415 = k415;
					printf("apply-415 c: completion at t=%u ms slot %u:"
					    " %08x %08x %08x %08x code %u\n", i415 * 5u + 5u, k415,
					    rd(e), rd(e + 4u), rd(e + 8u), rd(e + 0xcu),
					    (rd(e + 8u) >> 24) & 0xffu);
					break;
				}
			}
			if (seen415 != 0xffffffffu)
				break;
		}
		if (seen415 == 0xffffffffu)
			printf("apply-415 c: no completion in 500 ms\n");

		printf("apply-415 d: after: ee 0x%08x mh 0x%08x cmd rp 0x%08x wp 0x%08x ch20 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48),
		    rd(pcie_dma_extra + cofs415 + 0x1cu), rd(pcie_dma_extra + cofs415 + 0x24u),
		    rd(pcie_dma_extra + 20u * 0x2cu));
		printf("apply-415 e: sfr buffer %08x %08x %08x %08x | %08x %08x %08x %08x\n",
		    rd(sbuf415 + 0x0u), rd(sbuf415 + 0x4u), rd(sbuf415 + 0x8u), rd(sbuf415 + 0xcu),
		    rd(sbuf415 + 0x10u), rd(sbuf415 + 0x14u), rd(sbuf415 + 0x18u), rd(sbuf415 + 0x1cu));

		/* now the channel question again, with SFR done */
		if (rd(bar0.base + 0x128) == 2u) {
			uint32_t cw415 = rd(pcie_dma_extra + cofs415 + 0x24u);
			wr(pcie_dma_extra + cofs415 + 0x24u, cw415 + 0x10u);
			wr(tre415 + 0x00u, 0u);
			wr(tre415 + 0x04u, 0u);
			wr(tre415 + 0x08u, 0u);
			wr(tre415 + 0x0cu, 0x14120000u);	/* START_CHAN(20) */
			__asm__ __volatile__("dc civac, %0" :: "r"(tre415) : "memory");
			__asm__ __volatile__("dsb sy" ::: "memory");
			wr(bar0.base + 0x74u, 0u);
			wr(bar0.base + 0x70u, cw415 + 0x10u);
			printf("apply-415 f: START_CHAN(20) after sfr, wp 0x%08x\n", cw415 + 0x10u);
			for (i415 = 0; i415 < 60u; i415++) {
				sleep_ms(5);
				if (rd(bar0.base + 0x128) != 2u || (rd(bar0.base + 0x48) & 0xff00u) != 0x0200u) {
					printf("apply-415 g: t=%u ms ee 0x%08x mh 0x%08x ch20 0x%08x\n",
					    i415 * 5u + 5u, rd(bar0.base + 0x128), rd(bar0.base + 0x48),
					    rd(pcie_dma_extra + 20u * 0x2cu));
					break;
				}
			}
			printf("apply-415 h: end ee 0x%08x mh 0x%08x ch20 0x%08x rp 0x%08x wp 0x%08x\n",
			    rd(bar0.base + 0x128), rd(bar0.base + 0x48),
			    rd(pcie_dma_extra + 20u * 0x2cu), rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu),
			    rd(pcie_dma_extra + 20u * 0x2cu + 0x24u));
		} else {
			printf("apply-415 f: device is out of amss already, skipping the start command\n");
		}
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1
assert "apply-415" not in src

a = "pcie_mhi_data != 34u && pcie_chanstart != 0"
assert src.count(a) == 1
src = src.replace(a, "pcie_mhi_data != 34u && pcie_mhi_data != 35u && pcie_chanstart != 0")
b = "pcie_mhi_data != 34u) wr(pcie_dma_extra + 20 * 0x2c"
assert src.count(b) == 1
src = src.replace(b, "pcie_mhi_data != 34u && pcie_mhi_data != 35u) wr(pcie_dma_extra + 20 * 0x2c")

i = src.index(END)
src = src[:i] + BLOCK + src[i:]
assert src.count("apply-415 h:") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-415 ok")
