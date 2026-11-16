#!/usr/bin/env python3
"""apply-401: the pre-download block never ran -- drop the smmu_state term and prove reach."""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
OLD = ("\tif (pcie_mhi_data == 23u && smmu_state == 1 && pcie_dma_extra != 0) {\n"
       "\t\tuint64_t rddm_iova = PCIE_EXTRA_IOVA + 0x500000ull;")
NEW = ("\tprintf(\"apply-401 reach: mhi_data %u smmu %u dma 0x%llx ee 0x%08x\\n\",\n"
       "\t    pcie_mhi_data, smmu_state, (unsigned long long)pcie_dma_extra, rd(bar0.base + 0x128));\n"
       "\tif (pcie_mhi_data == 23u && pcie_dma_extra != 0) {\n"
       "\t\tuint64_t rddm_iova = PCIE_EXTRA_IOVA + 0x500000ull;")

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(OLD) == 1, "pre block not found"
assert "apply-401" not in src
src = src.replace(OLD, NEW)
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-401 ok")
