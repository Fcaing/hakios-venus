#!/usr/bin/env python3
"""apply-433: pcie_chzero=2 leaves LOOPBACK/DIAG running but publishes IPCR as disabled.

p477/p478 showed that writing chstate 0 for all six channels keeps AMSS from ever
booting (EE stuck at 1 for 118 s).  The venus DT gives ch20 "auto-start", so the
firmware starts it itself; publishing it as disabled probably fights that.  Test the
narrow case: only ch20/ch21 get 0, everything else keeps 0x0202.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert "apply-433" not in src, "apply-433 already present"

old = "wr(pcie_dma_extra + o3 + 0x00, (pcie_chzero != 0u ? 0u : 2u) | (2u << 8));"
new = ("/* apply-433: chzero 2 = only the ipcr pair is published disabled */\n"
       "\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x00,\n"
       "\t\t\t\t\t\t\t\t\t    ((pcie_chzero == 1u ||\n"
       "\t\t\t\t\t\t\t\t\t      (pcie_chzero == 2u && (chans[i3] == 20u || chans[i3] == 21u))) ?\n"
       "\t\t\t\t\t\t\t\t\t     0u : 2u) | (2u << 8));")
assert src.count(old) == 1, "chzero write"
src = src.replace(old, new)

io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-433 ok")
