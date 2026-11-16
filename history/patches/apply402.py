#!/usr/bin/env python3
"""apply-402: the pre-download block was gated on pcie_mhi_data, which is still 0 there.

apply-401 proved it: at the bhi handshake the variable reads 0 even though the cmdline says
23, because that boot argument is parsed much later than the bhi handshake.  Parse it right
where it is needed, then the block can arm BHIE RX before the image is transferred.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
OLD = ("\tprintf(\"apply-401 reach: mhi_data %u smmu %u dma 0x%llx ee 0x%08x\\n\",\n")
NEW = ("\t{\n"
       "\t\tuint32_t v402 = 0;\n"
       "\n"
       "\t\tif (PE_parse_boot_argn(\"pcie_mhi_data\", &v402, sizeof(v402)))\n"
       "\t\t\tpcie_mhi_data = v402;\n"
       "\t}\n"
       "\tprintf(\"apply-402 reach: mhi_data %u smmu %u dma 0x%llx ee 0x%08x\\n\",\n")

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(OLD) == 1, "reach print not found"
assert "apply-402" not in src
src = src.replace(OLD, NEW)
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-402 ok")
