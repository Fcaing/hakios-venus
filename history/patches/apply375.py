P = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(P).read()

a = "static uint32_t pcie_chrebuild;\t/* apply-373"
assert s.count(a) == 1
s = s.replace(a, "static uint32_t pcie_dtbch;\t/* apply-375: set ch ctxt per venus dtb */\n" + a)

b = 'PE_parse_boot_argn("pcie_chrebuild", &pcie_chrebuild, sizeof(pcie_chrebuild));'
assert s.count(b) == 1
s = s.replace(b, b + '\n\tPE_parse_boot_argn("pcie_dtbch", &pcie_dtbch, sizeof(pcie_dtbch));')

c = 'if (pcie_ch_ee != 0) {\n\t\t\t\t\tuint32_t old20'
assert s.count(c) == 1, s.count(c)

blk = r'''if (pcie_dtbch != 0) {
					uint32_t o20 = 0x2000 + 20 * 0x2c, o21 = 0x2000 + 21 * 0x2c;
					wr(pcie_dma_extra + o20, 1u);
					wr(pcie_dma_extra + o20 + 0x04, 1u);
					wr(pcie_dma_extra + o20 + 0x08, 1u);
					wr(pcie_dma_extra + o21, 1u);
					wr(pcie_dma_extra + o21 + 0x04, 0u);
					wr(pcie_dma_extra + o21 + 0x08, 1u);
					__asm__ __volatile__("dc civac, %0" :: "r"(pcie_dma_extra + o20) : "memory");
					__asm__ __volatile__("dc civac, %0" :: "r"(pcie_dma_extra + o21) : "memory");
					__asm__ __volatile__("dsb sy" ::: "memory");
					printf("pcie: 5:   21: apply-375 dtb ctxt: c20 %08x %08x %08x c21 %08x %08x %08x mh 0x%08x\n",
					       rd(pcie_dma_extra + o20), rd(pcie_dma_extra + o20 + 0x04), rd(pcie_dma_extra + o20 + 0x08),
					       rd(pcie_dma_extra + o21), rd(pcie_dma_extra + o21 + 0x04), rd(pcie_dma_extra + o21 + 0x08),
					       rd(bar0.base + 0x3c));
				}
				''' + c

s = s.replace(c, blk)
open(P, "w").write(s)
print("apply-375 ok")
