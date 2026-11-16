#!/usr/bin/env python3
"""apply-432: make the starflow block wait for EE=2 before it touches anything.

p477 ran the whole star sequence while the device was still in EE=1 (SBL): the block
sits inside the step-5 probe and AMSS had not finished booting, so the STARTs went to
an engine that had not been handed over yet.  Wait for the EE register to read 2
(AMSS), up to 3 s, and print how long it took.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert "apply-432" not in src, "apply-432 already present"

anchor = "if (pcie_starflow != 0 && pcie_mhi_data == 50u && smmu_state == 1 && pcie_dma_extra != 0) {\n"
assert src.count(anchor) == 1, "starflow block"

wait = (
    "\t\t{\n"
    "\t\t\tuint32_t w432;\n"
    "\t\t\tfor (w432 = 0; w432 < 600u; w432++) {\n"
    "\t\t\t\tif (rd(bar0.base + 0x128) == 2u)\n"
    "\t\t\t\t\tbreak;\n"
    "\t\t\t\tsleep_ms(5);\n"
    "\t\t\t}\n"
    "\t\t\tprintf(\"apply-432 waited %u ms: ee 0x%08x mh 0x%08x\\n\",\n"
    "\t\t\t    w432 * 5u, rd(bar0.base + 0x128), rd(bar0.base + 0x48));\n"
    "\t\t}\n"
)

src = src.replace(anchor, anchor + wait)
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-432 ok")
