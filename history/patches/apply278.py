import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
src = io.open(p, encoding="utf-8").read()

a1 = "					wr(bar0.base + 0x88, 0xb0000000u);"
a2 = "					wr(bar0.base + 0xa0, 0xb0000000u);"
assert src.count(a1) == 1, src.count(a1)
assert src.count(a2) == 1, src.count(a2)

new1 = ("					/* apply-278: the device was told its control/data window runs\n"
        "					 * to 0xb0000000, but only 0xa0200000..0xa0a00000 is mapped\n"
        "					 * in the SMMU.  Keep the window inside what we mapped. */\n"
        "					wr(bar0.base + 0x88, (uint32_t)(PCIE_EXTRA_IOVA + PCIE_EXTRA_SIZE));")
new2 = "					wr(bar0.base + 0xa0, (uint32_t)(PCIE_EXTRA_IOVA + PCIE_EXTRA_SIZE));"
src = src.replace(a1, new1).replace(a2, new2)

a3 = '					       ctxt, ering, cring, cfg, rd(bar0.base + 0x10));'
assert src.count(a3) == 1
src = src.replace(a3, a3 + '\n\t\t\t\t\tprintf("pcie: 5:   21: apply-278 window 0x%08x..0x%08x (mapped only)\\n",\n\t\t\t\t\t       (uint32_t)ctxt, (uint32_t)(PCIE_EXTRA_IOVA + PCIE_EXTRA_SIZE));')

io.open(p, "w", encoding="utf-8").write(src)
print("apply-278 written", len(src))