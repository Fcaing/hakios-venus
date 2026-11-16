#!/usr/bin/env python3
"""apply-431: publish chstate 0 in the early context write, the way star does.

star's mhi_ready() writes only type/index/rbase/rlen/rp/wp while SBL owns MHI and
leaves chstate = 0 (disabled); it raises the channel to 0x201 only after mission
mode, right before START_CHAN.  We have always written 0x202 (RUNNING) at the
early point, which tells the firmware the channel is already running before its
IPCR client exists.  pcie_chzero=1 selects star's value.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert "apply-431" not in src, "apply-431 already present"

# 1. declaration
anchor = "static uint32_t pcie_starflow;"
assert src.count(anchor) == 1, "starflow decl"
src = src.replace(anchor,
    "static uint32_t pcie_chzero;\t/* apply-431: publish chstate 0 early, as star does */\n" + anchor)

# 2. boot-arg parse
anchor = '\tPE_parse_boot_argn("pcie_starflow", &pcie_starflow, sizeof(pcie_starflow));\n'
assert src.count(anchor) == 1, "starflow parse"
src = src.replace(anchor, anchor +
    '\tPE_parse_boot_argn("pcie_chzero", &pcie_chzero, sizeof(pcie_chzero));\n')

# 3. the early context word
anchor = "wr(pcie_dma_extra + o3 + 0x00, 2u | (2u << 8));"
assert src.count(anchor) == 1, "ctx word0 write"
src = src.replace(anchor,
    "wr(pcie_dma_extra + o3 + 0x00, (pcie_chzero != 0u ? 0u : 2u) | (2u << 8));")

io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-431 ok")
