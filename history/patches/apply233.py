import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(p, encoding="utf-8").read()
n0 = len(s)

def rep(old, new, tag):
    global s
    if s.count(old) != 1:
        raise SystemExit("anchor %s count=%d" % (tag, s.count(old)))
    s = s.replace(old, new, 1)

# 0: the boot-time vote mask, without the pipe clock (star opens it after the phy)
rep("#define VOTE_1_MASK\t\t\t0x0000003fu /* bits 0..5: the pipe clock is bit 4 */",
    "#define VOTE_1_MASK\t\t\t0x0000003fu /* bits 0..5: the pipe clock is bit 4 */\n"
    "#define VOTE_1_BOOT\t\t\t0x0000002fu /* star stage 4: cfg/master/slave/aux/q2a, NO pipe */",
    "vote-boot")

# 1: the votable power domain, before the collapse bit is cleared
rep("\t\tgdscr = rd(gcc.base + GCC_GDSCR);\n"
    "\t\tprintf(\"pcie: 2:   GDSCR 0x6b004 = 0x%08x -> clear bit 0 (SW_COLLAPSE)\\n\", gdscr);",
    "\t\tprintf(\"pcie: 2:   star stage 3: the votable power domain 0x52128 0x%08x -> bit 0 clear\\n\",\n"
    "\t\t       rd(gcc.base + 0x52128));\n"
    "\t\twr(gcc.base + 0x52128, rd(gcc.base + 0x52128) & ~1u);\n"
    "\t\tgdscr = rd(gcc.base + GCC_GDSCR);\n"
    "\t\tprintf(\"pcie: 2:   GDSCR 0x6b004 = 0x%08x -> clear bit 0 (SW_COLLAPSE)\\n\", gdscr);",
    "52128")

# 2: retain the flip-flops of the domain that just came up
rep("\t\tpcie_note(\"pcie: 2: gdscr 0x%08x after %u polls; \", gdscr, i + 1);",
    "\t\tpcie_note(\"pcie: 2: gdscr 0x%08x after %u polls; \", gdscr, i + 1);\n"
    "\t\twr(gcc.base + GCC_GDSCR, rd(gcc.base + GCC_GDSCR) | (1u << 11));\n"
    "\t\tprintf(\"pcie: 2:   star stage 3: the domain kept (GDSCR bit 11): 0x6b004 = 0x%08x\\n\",\n"
    "\t\t       rd(gcc.base + GCC_GDSCR));",
    "retain")

# 3: the root's RCGs before the votes, and the votes themselves without the pipe clock
rep("\t\tsleep_ms(PCIE_AFTER_SETTLE_MS);\n"
    "\t\tprintf(\"pcie: 2:   the clock votes, now that the domain is on: 0x52008 |= 0x%08x, 0x52000 |= 0x%08x\\n\",\n"
    "\t\t       VOTE_1_MASK, VOTE_0_MASK);\n"
    "\t\twr(gcc.base + GCC_VOTE_1, rd(gcc.base + GCC_VOTE_1) | VOTE_1_MASK);",
    "\t\t{\n"
    "\t\t\tuint32_t mux = rd(gcc.base + 0x6b054);\n"
    "\t\t\tuint32_t src = rd(gcc.base + 0x6b05c);\n"
    "\t\t\tuint32_t cfg = rd(gcc.base + 0x6b058);\n"
    "\t\t\tuint32_t h;\n"
    "\t\t\twr(gcc.base + 0x6b054, mux & ~3u);                    /* the phy's pipe, extern */\n"
    "\t\t\twr(gcc.base + 0x6b05c, (src & ~0x371fu) | 1u);        /* aux = XO / 1 */\n"
    "\t\t\twr(gcc.base + 0x6b058, cfg | 1u);\n"
    "\t\t\tfor (h = 0; h < 200 && (rd(gcc.base + 0x6b058) & 1u); h++)\n"
    "\t\t\t\tsleep_us(10);\n"
    "\t\t\tprintf(\"pcie: 2:   star stage 4: pipe mux 0x6b054 0x%08x -> 0x%08x, aux 0x6b05c 0x%08x -> 0x%08x, 0x6b058 0x%08x -> 0x%08x\\n\",\n"
    "\t\t\t       mux, rd(gcc.base + 0x6b054), src, rd(gcc.base + 0x6b05c), cfg, rd(gcc.base + 0x6b058));\n"
    "\t\t}\n"
    "\t\tsleep_ms(PCIE_AFTER_SETTLE_MS);\n"
    "\t\tprintf(\"pcie: 2:   the clock votes, now that the domain is on: 0x52008 |= 0x%08x, 0x52000 |= 0x%08x\\n\",\n"
    "\t\t       VOTE_1_BOOT, VOTE_0_MASK);\n"
    "\t\twr(gcc.base + GCC_VOTE_1, rd(gcc.base + GCC_VOTE_1) | VOTE_1_BOOT);",
    "rcg+votes")

# 4: star waits for the four roots to stop reporting a halt
rep("\t\tpcie_note(\"clkref 0x%08x aux 0x%08x; \", rd(gcc.base + GCC_CLKREF_EN), rd(gcc.base + 0x6b028));",
    "\t\t{\n"
    "\t\t\tuint32_t h, halted = 1u;\n"
    "\t\t\tfor (h = 0; h < 200; h++) {\n"
    "\t\t\t\thalted = (rd(gcc.base + 0x6b024) | rd(gcc.base + 0x6b014) |\n"
    "\t\t\t\t          rd(gcc.base + 0x6b028) | rd(gcc.base + 0x6b038)) & (1u << 31);\n"
    "\t\t\t\tif (!halted)\n"
    "\t\t\t\t\tbreak;\n"
    "\t\t\t\tsleep_us(50);\n"
    "\t\t\t}\n"
    "\t\t\tprintf(\"pcie: 2:   star stage 4: cfg 0x6b024 0x%08x, mstr 0x6b01c 0x%08x, slv 0x6b014 0x%08x, pipe 0x6b030 0x%08x (%s)\\n\",\n"
    "\t\t\t       rd(gcc.base + 0x6b024), rd(gcc.base + 0x6b01c), rd(gcc.base + 0x6b014),\n"
    "\t\t\t       rd(gcc.base + 0x6b030), halted ? \"still halted\" : \"running\");\n"
    "\t\t}\n"
    "\t\tpcie_note(\"clkref 0x%08x aux 0x%08x; \", rd(gcc.base + GCC_CLKREF_EN), rd(gcc.base + 0x6b028));",
    "halt-wait")

# 5: step 3 holds PERST# low and pulses the roots before touching the phy
rep("\tprintf(\"pcie: 3: %u writes of the vendor's PHY sequence at 0x%x\\n\", VENUS_PCIE_PHY_SEQ_LEN,\n"
    "\t       phy.phys);",
    "\tif (need(&tlmm)) {\n"
    "\t\tvm_offset_t pin = tlmm.base + PERST_PIN * TLMM_PIN_STRIDE;\n"
    "\t\twr(pin + TLMM_CFG, TLMM_CFG_OE);\n"
    "\t\twr(pin + TLMM_IO, 0);\n"
    "\t\tprintf(\"pcie: 3:   star stage 5: PERST# (pin %u) held low 0x%08x through the phy\\n\",\n"
    "\t\t       PERST_PIN, rd(pin + TLMM_IO));\n"
    "\t}\n"
    "\tpause_us(1000);\n"
    "\twr(gcc.base + 0x6b000, rd(gcc.base + 0x6b000) | 1u);\n"
    "\tpause_us(1000);\n"
    "\twr(gcc.base + 0x6b000, rd(gcc.base + 0x6b000) & ~1u);\n"
    "\twr(gcc.base + 0x6c01c, rd(gcc.base + 0x6c01c) | 1u);\n"
    "\tpause_us(1000);\n"
    "\twr(gcc.base + 0x6c01c, rd(gcc.base + 0x6c01c) & ~1u);\n"
    "\tprintf(\"pcie: 3:   star stage 5: the root and the phy pulsed (0x6b000 0x%08x, 0x6c01c 0x%08x)\\n\",\n"
    "\t       rd(gcc.base + 0x6b000), rd(gcc.base + 0x6c01c));\n"
    "\tprintf(\"pcie: 3: %u writes of the vendor's PHY sequence at 0x%x\\n\", VENUS_PCIE_PHY_SEQ_LEN,\n"
    "\t       phy.phys);",
    "perst+resets")

# 6: the pipe clock only after the phy has its sequence in
rep("\tsleep_ms(1);\n\t/* Linux waits for the PCS status bit to become CLEAR (phy-qcom-qmp-pcie.c:4870). */",
    "\tsleep_ms(1);\n"
    "\twr(gcc.base + GCC_VOTE_1, rd(gcc.base + GCC_VOTE_1) | 0x10u);\n"
    "\tprintf(\"pcie: 3:   star stage 7: the pipe clock on after the phy: 0x52008 = 0x%08x\\n\",\n"
    "\t       rd(gcc.base + GCC_VOTE_1));\n"
    "\t/* Linux waits for the PCS status bit to become CLEAR (phy-qcom-qmp-pcie.c:4870). */",
    "pipe-on")

# 7: the clock request line, alt1 with a pull-up, as the vendor sets it
rep("#define WLAN_EN_PIN 64\n",
    "#define WLAN_EN_PIN 64\n#define CLKREQ_PIN 95\n\n"
    "/* star stage 9: alt1, pull-up, 2 mA input: the endpoint asks for the reference clock here */\n"
    "static void\nclkreq_pin(void)\n{\n"
    "\tvm_offset_t pin = tlmm.base + CLKREQ_PIN * TLMM_PIN_STRIDE;\n"
    "\tuint32_t cfg = rd(pin + TLMM_CFG);\n"
    "\twr(pin + TLMM_CFG, (cfg & ~0x3ffu) | 7u);\n"
    "\tprintf(\"pcie: 4:   CLKREQ# (pin %u) alt1 pull-up: CFG 0x%08x -> 0x%08x\\n\",\n"
    "\t       CLKREQ_PIN, cfg, rd(pin + TLMM_CFG));\n}\n",
    "clkreq-fn")

# 8: call it before the pause that precedes WLAN_EN
rep("\tprintf(\"pcie: 4:   the radio's rails are voted\\n\");\n\tpcie_note(\"radio rails voted; \");\n\tsleep_ms(100);",
    "\tprintf(\"pcie: 4:   the radio's rails are voted\\n\");\n"
    "\tpcie_note(\"radio rails voted; \");\n"
    "\tclkreq_pin();\n"
    "\tsleep_ms(100);",
    "clkreq-call")

open(p, "w", encoding="utf-8").write(s)
print("ok, %d -> %d bytes" % (n0, len(s)))