#!/usr/bin/env python3
"""apply-430: replicate star's post-mission IPCR bring-up, with completion checks.

star (lemonade_wifi.c:1230-1246) does, *after* EE=2:
  ctx ch20/21 <- 0x201 / type / index 1 / rbase / rlen 0x200 / rp=wp=rbase
  START_CHAN(20), wait for CMD_COMPLETION with code 1 (3 s)
  START_CHAN(21), same
This round does exactly that, and reports what the event ring actually delivers.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

DECL = ("static uint32_t pcie_starflow;\t/* apply-430: after ee 2, publish the ipcr contexts and\n"
        "\t\t\t\t * start the channels exactly the way star's driver does. */\n")

BLOCK = r'''	/* apply-430: star's order - demote the channels to ENABLED, send START_CHAN,
	 * and demand a CMD_COMPLETION with code 1 for each. */
	if (pcie_starflow != 0 && pcie_mhi_data == 50u && smmu_state == 1 && pcie_dma_extra != 0) {
		uint32_t sf, k, wait_ms, hits;
		uint64_t sbase, swp;

		printf("apply-430 t0: ee 0x%08x mh 0x%08x ctrl 0x%08x ch20 0x%08x ch21 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48), rd(bar0.base + 0x38),
		    rd(pcie_dma_extra + 20 * 0x2c), rd(pcie_dma_extra + 21 * 0x2c));
		sleep_ms(2000);
		printf("apply-430 settled: ee 0x%08x mh 0x%08x ch20 0x%08x ch21 0x%08x\n",
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48),
		    rd(pcie_dma_extra + 20 * 0x2c), rd(pcie_dma_extra + 21 * 0x2c));

		/* the two data channel contexts, star style */
		wr(pcie_dma_extra + 20 * 0x2c + 0x00, 0x201u);
		wr(pcie_dma_extra + 20 * 0x2c + 0x04, 1u);
		wr(pcie_dma_extra + 20 * 0x2c + 0x08, 1u);
		wr(pcie_dma_extra + 20 * 0x2c + 0x0c, (uint32_t)(PCIE_EXTRA_IOVA + 0x3600));
		wr(pcie_dma_extra + 20 * 0x2c + 0x14, 0x200u);
		wr(pcie_dma_extra + 20 * 0x2c + 0x1c, (uint32_t)(PCIE_EXTRA_IOVA + 0x3600));
		wr(pcie_dma_extra + 20 * 0x2c + 0x24, (uint32_t)(PCIE_EXTRA_IOVA + 0x3600));
		wr(pcie_dma_extra + 21 * 0x2c + 0x00, 0x201u);
		wr(pcie_dma_extra + 21 * 0x2c + 0x04, 2u);
		wr(pcie_dma_extra + 21 * 0x2c + 0x08, 1u);
		wr(pcie_dma_extra + 21 * 0x2c + 0x0c, (uint32_t)(PCIE_EXTRA_IOVA + 0x3800));
		wr(pcie_dma_extra + 21 * 0x2c + 0x14, 0x200u);
		wr(pcie_dma_extra + 21 * 0x2c + 0x1c, (uint32_t)(PCIE_EXTRA_IOVA + 0x3800));
		wr(pcie_dma_extra + 21 * 0x2c + 0x24, (uint32_t)(PCIE_EXTRA_IOVA + 0x3800));
		for (k = 0; k < 0x100; k += 64) {
			__asm__ __volatile__("dc civac, %0" :: "r"(pcie_dma_extra + 20 * 0x2c + k) : "memory");
			__asm__ __volatile__("dc civac, %0" :: "r"(pcie_dma_extra + 21 * 0x2c + k) : "memory");
		}
		__asm__ __volatile__("dsb sy" ::: "memory");
		printf("apply-430 ctx: ch20 0x%08x rbase 0x%08x ch21 0x%08x rbase 0x%08x\n",
		    rd(pcie_dma_extra + 20 * 0x2c), rd(pcie_dma_extra + 20 * 0x2c + 0x0c),
		    rd(pcie_dma_extra + 21 * 0x2c), rd(pcie_dma_extra + 21 * 0x2c + 0x0c));

		for (sf = 0; sf < 2u; sf++) {
			uint32_t sch = (sf == 0u) ? 20u : 21u;
			uint64_t cptr_iova = PCIE_EXTRA_IOVA + 0x7000 + sf * 16;
			uint32_t kw;

			wr(pcie_dma_extra + 0x7000 + sf * 16 + 0, 0u);
			wr(pcie_dma_extra + 0x7000 + sf * 16 + 4, 0u);
			wr(pcie_dma_extra + 0x7000 + sf * 16 + 8, 0u);
			wr(pcie_dma_extra + 0x7000 + sf * 16 + 12, (sch << 24) | (18u << 16));
			wr(pcie_dma_extra + 0x2400 + 0x1c, (uint32_t)(PCIE_EXTRA_IOVA + 0x7000));
			wr(pcie_dma_extra + 0x2400 + 0x24, (uint32_t)(PCIE_EXTRA_IOVA + 0x7000 + (sf + 1) * 16));
			for (k = 0; k < 0x100; k += 64) {
				__asm__ __volatile__("dc civac, %0" :: "r"(pcie_dma_extra + 0x7000 + k) : "memory");
				__asm__ __volatile__("dc civac, %0" :: "r"(pcie_dma_extra + 0x2400 + k) : "memory");
			}
			__asm__ __volatile__("dsb sy" ::: "memory");
			wr(bar0.base + 0x70, (uint32_t)(PCIE_EXTRA_IOVA + 0x7000 + (sf + 1) * 16));
			printf("apply-430 start%u: tre 0x%08x rung 0x70, waiting for completion\n",
			    sch, (uint32_t)cptr_iova);

			hits = 0u;
			for (wait_ms = 0; wait_ms < 3000u; wait_ms++) {
				uint32_t slot;

				for (slot = 0; slot < 8u; slot++) {
					uint32_t d0 = rd(pcie_dma_extra + 0x4000 + slot * 16);
					uint32_t d3 = rd(pcie_dma_extra + 0x4000 + slot * 16 + 12);

					if (((d3 >> 16) & 0xffu) == 0x21u && d0 == (uint32_t)cptr_iova) {
						printf("apply-430 start%u: COMPLETION in er0[%u] after %u ms, code %u\n",
						    sch, slot, wait_ms, (rd(pcie_dma_extra + 0x4000 + slot * 16 + 8) >> 16) & 0xffu);
						hits = 1u;
						break;
					}
				}
				if (hits != 0u) {
					break;
				}
				sleep_ms(1);
			}
			if (hits == 0u) {
				printf("apply-430 start%u: no completion in 3 s (ee 0x%08x mh 0x%08x ch 0x%08x)\n",
				    sch, rd(bar0.base + 0x128), rd(bar0.base + 0x48),
				    rd(pcie_dma_extra + sch * 0x2c));
			}
		}

		/* what the event ring holds now, so a silent run is still informative */
		sbase = PCIE_EXTRA_IOVA + 0x4000;
		for (k = 0; k < 8u; k++) {
			printf("apply-430 er0[%u]: %08x %08x %08x %08x\n", k,
			    rd(pcie_dma_extra + 0x4000 + k * 16), rd(pcie_dma_extra + 0x4000 + k * 16 + 4),
			    rd(pcie_dma_extra + 0x4000 + k * 16 + 8), rd(pcie_dma_extra + 0x4000 + k * 16 + 12));
		}
		swp = PCIE_EXTRA_IOVA + 0x4000;
		printf("apply-430 end: er0 base 0x%08x rp 0x%08x wp 0x%08x ee 0x%08x mh 0x%08x ch20 0x%08x ch21 0x%08x\n",
		    (uint32_t)sbase, rd(pcie_dma_extra + 0x201c), rd(pcie_dma_extra + 0x2024),
		    rd(bar0.base + 0x128), rd(bar0.base + 0x48),
		    rd(pcie_dma_extra + 20 * 0x2c), rd(pcie_dma_extra + 21 * 0x2c));
		(void)swp;
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert "apply-430" not in src, "apply-430 already present"

anchor = "static uint32_t pcie_socreset;\t/* apply-377: host requested soc reset through 0xb0 */\n"
assert src.count(anchor) == 1, "decl anchor not unique"
src = src.replace(anchor, DECL + anchor)

old_gate = "\t\t\t\tif (pcie_chanstart != 0) {\n\t\t\t\t\tstatic const uint32_t cch[4] = { 0, 1, 20, 21 };"
assert src.count(old_gate) == 1, "chanstart gate not unique (%d)" % src.count(old_gate)
src = src.replace(old_gate,
                  "\t\t\t\tif (pcie_chanstart != 0 && pcie_starflow == 0u) {\n\t\t\t\t\tstatic const uint32_t cch[4] = { 0, 1, 20, 21 };")

parse_anchor = '\tPE_parse_boot_argn("pcie_socreset", &pcie_socreset, sizeof(pcie_socreset));\n'
assert src.count(parse_anchor) == 1, "parse anchor not unique"
src = src.replace(parse_anchor, parse_anchor +
                  '\tPE_parse_boot_argn("pcie_starflow", &pcie_starflow, sizeof(pcie_starflow));\n')

assert src.count(END) == 1, "end marker not unique"
src = src.replace(END, BLOCK + END)

io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-430 ok")
