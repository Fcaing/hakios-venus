import io, re
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
src = open(p, encoding="utf-8").read()
orig = len(src)
def sub(old, new, tag):
    global src
    n = src.count(old)
    assert n == 1, (tag, n)
    src = src.replace(old, new)
    print("ok", tag)

# 1) the mask variable
old = "static uint32_t pcie_bhi_size;"
i = src.index(old)
j = src.index("\n", i)
src = src[:j+1] + "static uint32_t pcie_star_mask = 0x1fu;\t/* apply-235: which of the star stages run */\n" + src[j+1:]
print("ok mask var")

# 2) parse the boot arg
sub('\tprintf("pcie: 1: every register of the always-on part has been read\\n");\n',
    '\tprintf("pcie: 1: every register of the always-on part has been read\\n");\n'
    '\t{\n'
    '\t\tuint32_t mask = 0;\n'
    '\t\tif (PE_parse_boot_argn("pcie_star_mask", &mask, sizeof(mask)))\n'
    '\t\t\tpcie_star_mask = mask;\n'
    '\t\tprintf("pcie: 1: apply-235: the star stages that run 0x%x\\n", pcie_star_mask);\n'
    '\t}\n', "parse")

# 3) stage 3: the votable power domain
sub('\t\tprintf("pcie: 2:   star stage 3: the votable power domain 0x52128 0x%08x -> bit 0 clear\\n",\n'
    '\t\t       rd(gcc.base + 0x52128));\n'
    '\t\twr(gcc.base + 0x52128, rd(gcc.base + 0x52128) & ~1u);\n',
    '\t\tif (pcie_star_mask & 1u) {\n'
    '\t\t\tprintf("pcie: 2:   star stage 3: the votable power domain 0x52128 0x%08x -> bit 0 clear\\n",\n'
    '\t\t\t       rd(gcc.base + 0x52128));\n'
    '\t\t\twr(gcc.base + 0x52128, rd(gcc.base + 0x52128) & ~1u);\n'
    '\t\t}\n', "stage3 votable")

# 4) stage 3: the retain bit
sub('\t\twr(gcc.base + GCC_GDSCR, rd(gcc.base + GCC_GDSCR) | (1u << 11));\n'
    '\t\tprintf("pcie: 2:   star stage 3: the domain kept (GDSCR bit 11): 0x6b004 = 0x%08x\\n",\n'
    '\t\t       rd(gcc.base + GCC_GDSCR));\n',
    '\t\tif (pcie_star_mask & 1u) {\n'
    '\t\t\twr(gcc.base + GCC_GDSCR, rd(gcc.base + GCC_GDSCR) | (1u << 11));\n'
    '\t\t\tprintf("pcie: 2:   star stage 3: the domain kept (GDSCR bit 11): 0x6b004 = 0x%08x\\n",\n'
    '\t\t\t       rd(gcc.base + GCC_GDSCR));\n'
    '\t\t}\n', "stage3 retain")

# 5) stage 4: the rcg block
sub('\t\t{\n\t\t\tuint32_t mux = rd(gcc.base + 0x6b054);',
    '\t\tif (pcie_star_mask & 2u) {\n\t\t\tuint32_t mux = rd(gcc.base + 0x6b054);', "stage4 rcg")

# 6) stage 4: the votes
sub('\t\tprintf("pcie: 2:   the clock votes, now that the domain is on: 0x52008 |= 0x%08x, 0x52000 |= 0x%08x\\n",\n'
    '\t\t       VOTE_1_BOOT, VOTE_0_MASK);\n'
    '\t\twr(gcc.base + GCC_VOTE_1, rd(gcc.base + GCC_VOTE_1) | VOTE_1_BOOT);\n',
    '\t\tuint32_t v1 = 0x0000003fu;\n'
    '\t\tif (pcie_star_mask & 2u) {\n'
    '\t\t\tv1 = VOTE_1_BOOT;\n'
    '\t\t\tif (!(pcie_star_mask & 8u))\n'
    '\t\t\t\tv1 |= 0x10u;\t/* the pipe clock, not deferred */\n'
    '\t\t}\n'
    '\t\tprintf("pcie: 2:   the clock votes, now that the domain is on: 0x52008 |= 0x%08x, 0x52000 |= 0x%08x\\n",\n'
    '\t\t       v1, VOTE_0_MASK);\n'
    '\t\twr(gcc.base + GCC_VOTE_1, rd(gcc.base + GCC_VOTE_1) | v1);\n', "stage4 votes")

# 7) phy_start: PERST held low
sub('\tif (need(&tlmm)) {\n'
    '\t\tvm_offset_t pin = tlmm.base + PERST_PIN * TLMM_PIN_STRIDE;\n'
    '\t\twr(pin + TLMM_CFG, TLMM_CFG_OE);\n'
    '\t\twr(pin + TLMM_IO, 0);\n'
    '\t\tprintf("pcie: 3:   star stage 5: PERST# (pin %u) held low 0x%08x through the phy\\n",\n'
    '\t\t       PERST_PIN, rd(pin + TLMM_IO));\n'
    '\t}\n',
    '\tif ((pcie_star_mask & 4u) && need(&tlmm)) {\n'
    '\t\tvm_offset_t pin = tlmm.base + PERST_PIN * TLMM_PIN_STRIDE;\n'
    '\t\twr(pin + TLMM_CFG, TLMM_CFG_OE);\n'
    '\t\twr(pin + TLMM_IO, 0);\n'
    '\t\tprintf("pcie: 3:   star stage 5: PERST# (pin %u) held low 0x%08x through the phy\\n",\n'
    '\t\t       PERST_PIN, rd(pin + TLMM_IO));\n'
    '\t}\n', "stage5 perst")

# 8) phy_start: the reset pulses
sub('\tsleep_us(1000);\n'
    '\twr(gcc.base + 0x6b000, rd(gcc.base + 0x6b000) | 1u);\n'
    '\tsleep_us(1000);\n'
    '\twr(gcc.base + 0x6b000, rd(gcc.base + 0x6b000) & ~1u);\n'
    '\twr(gcc.base + 0x6c01c, rd(gcc.base + 0x6c01c) | 1u);\n'
    '\tsleep_us(1000);\n'
    '\twr(gcc.base + 0x6c01c, rd(gcc.base + 0x6c01c) & ~1u);\n'
    '\tprintf("pcie: 3:   star stage 5: the root and the phy pulsed (0x6b000 0x%08x, 0x6c01c 0x%08x)\\n",\n'
    '\t       rd(gcc.base + 0x6b000), rd(gcc.base + 0x6c01c));\n',
    '\tif (pcie_star_mask & 4u) {\n'
    '\t\tsleep_us(1000);\n'
    '\t\twr(gcc.base + 0x6b000, rd(gcc.base + 0x6b000) | 1u);\n'
    '\t\tsleep_us(1000);\n'
    '\t\twr(gcc.base + 0x6b000, rd(gcc.base + 0x6b000) & ~1u);\n'
    '\t\twr(gcc.base + 0x6c01c, rd(gcc.base + 0x6c01c) | 1u);\n'
    '\t\tsleep_us(1000);\n'
    '\t\twr(gcc.base + 0x6c01c, rd(gcc.base + 0x6c01c) & ~1u);\n'
    '\t\tprintf("pcie: 3:   star stage 5: the root and the phy pulsed (0x6b000 0x%08x, 0x6c01c 0x%08x)\\n",\n'
    '\t\t       rd(gcc.base + 0x6b000), rd(gcc.base + 0x6c01c));\n'
    '\t}\n', "stage5 pulses")

# 9) phy_start: the pipe clock
sub('\tsleep_ms(1);\n'
    '\twr(gcc.base + GCC_VOTE_1, rd(gcc.base + GCC_VOTE_1) | 0x10u);\n'
    '\tprintf("pcie: 3:   star stage 7: the pipe clock on after the phy: 0x52008 = 0x%08x\\n",\n'
    '\t       rd(gcc.base + GCC_VOTE_1));\n',
    '\tif (pcie_star_mask & 8u) {\n'
    '\t\tsleep_ms(1);\n'
    '\t\twr(gcc.base + GCC_VOTE_1, rd(gcc.base + GCC_VOTE_1) | 0x10u);\n'
    '\t\tprintf("pcie: 3:   star stage 7: the pipe clock on after the phy: 0x52008 = 0x%08x\\n",\n'
    '\t\t       rd(gcc.base + GCC_VOTE_1));\n'
    '\t}\n', "stage7 pipe")

# 10) clkreq
sub('\tclkreq_pin();\n', '\tif (pcie_star_mask & 16u)\n\t\tclkreq_pin();\n', "clkreq")

open(p, "w", encoding="utf-8").write(src)
print("bytes", orig, "->", len(src), "235:", src.count("apply-235"))