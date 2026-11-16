#!/usr/bin/env python3
"""apply-434: pcie_chzero=3 publishes the IPCR pair as chstate 1 (ENABLED), not 2.

Facts so far: 0x0202 lets AMSS boot but the command ring is ignored; 0x0200 (chstate 0)
keeps AMSS from booting at all.  So the firmware reads these contexts during handover.
Try the middle value: ENABLED, not RUNNING.  If AMSS still boots and a later START_CHAN
finally completes, the channel state at handover was the whole story.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert "apply-434" not in src, "apply-434 already present"

old = ("((pcie_chzero == 1u ||\n"
       "\t\t\t\t\t\t\t\t\t      (pcie_chzero == 2u && (chans[i3] == 20u || chans[i3] == 21u))) ?\n"
       "\t\t\t\t\t\t\t\t\t     0u : 2u) | (2u << 8));")
new = ("/* apply-434: chzero 3 = the ipcr pair is published ENABLED, not RUNNING */\n"
       "\t\t\t\t\t\t\t\t\t    ((pcie_chzero == 3u && (chans[i3] == 20u || chans[i3] == 21u)) ?\n"
       "\t\t\t\t\t\t\t\t\t     1u :\n"
       "\t\t\t\t\t\t\t\t\t     ((pcie_chzero == 1u ||\n"
       "\t\t\t\t\t\t\t\t\t       (pcie_chzero == 2u && (chans[i3] == 20u || chans[i3] == 21u))) ?\n"
       "\t\t\t\t\t\t\t\t\t      0u : 2u)) | (2u << 8));")
assert src.count(old) == 1, "chzero write (apply-433 form)"
src = src.replace(old, new)

io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-434 ok")
