import io, re
F = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
src = open(F, encoding="utf-8", errors="surrogateescape").read()

# --- 1. statics ---
anchor = "static uint64_t pcie_fw_size;   /* apply-218: the size of amss.bin */\n"
assert src.count(anchor) == 1, "static anchor"
src = src.replace(anchor, anchor +
 "static uint32_t pcie_bhi_addr;  /* apply-232: override the BHI upload address */\n"
 "static uint32_t pcie_bhi_size;  /* apply-232: override the BHI upload size */\n")

# --- 2. doorbell block ---
old = """\t\t\t\twr(bar0.base + 0x10c,
\t\t\t\t    (uint32_t)((PCIE_EXTRA_IOVA + PCIE_EXTRA_DATA_OFF) >> 32));
\t\t\t\twr(bar0.base + 0x108,
\t\t\t\t    (uint32_t)(PCIE_EXTRA_IOVA + PCIE_EXTRA_DATA_OFF));
\t\t\t\twr(bar0.base + 0x110, (uint32_t)pcie_fw_size);
\t\t\t\tprintf("pcie: 5:   21: apply-224: bhi gets the whole image: addr 0x%llx size 0x%llx\\n",
\t\t\t\t    (unsigned long long)(PCIE_EXTRA_IOVA + PCIE_EXTRA_DATA_OFF),
\t\t\t\t    (unsigned long long)pcie_fw_size);
"""
new = """\t\t\t\t{
\t\t\t\t\tuint64_t bhi_addr = pcie_bhi_addr != 0 ?
\t\t\t\t\t    (uint64_t)pcie_bhi_addr :
\t\t\t\t\t    (PCIE_EXTRA_IOVA + PCIE_EXTRA_DATA_OFF);
\t\t\t\t\tuint64_t bhi_size = pcie_bhi_size != 0 ?
\t\t\t\t\t    (uint64_t)pcie_bhi_size : pcie_fw_size;

\t\t\t\t\twr(bar0.base + 0x10c, (uint32_t)(bhi_addr >> 32));
\t\t\t\t\twr(bar0.base + 0x108, (uint32_t)bhi_addr);
\t\t\t\t\twr(bar0.base + 0x110, (uint32_t)bhi_size);
\t\t\t\t\tprintf("pcie: 5:   21: apply-232: bhi gets addr 0x%llx size 0x%llx (fw 0x%llx)\\n",
\t\t\t\t\t    (unsigned long long)bhi_addr, (unsigned long long)bhi_size,
\t\t\t\t\t    (unsigned long long)pcie_fw_size);
\t\t\t\t}
"""
assert src.count(old) == 1, "doorbell anchor"
src = src.replace(old, new)

# --- 3. boot args in stage ---
anchor2 = "pcie_fw_size = fsize;\n"
assert src.count(anchor2) == 1, "stage anchor"
src = src.replace(anchor2, anchor2 + """\t/* apply-232: star's own working run handed the PBL only the first
\t * 512 KiB at 0xa0004000 (WIFI_DMA_SIZE / WIFI_DMA_IOVA).  Allow the
\t * upload window to be pointed at that staging page, or anywhere else,
\t * so the two configurations can be compared directly.
\t */
\t{
\t\tuint32_t a = 0, sz = 0;

\t\tif (PE_parse_boot_argn("pcie_bhi_addr", &a, sizeof(a)) && a != 0) {
\t\t\tpcie_bhi_addr = a;
\t\t}
\t\tif (PE_parse_boot_argn("pcie_bhi_size", &sz, sizeof(sz)) && sz != 0) {
\t\t\tpcie_bhi_size = sz;
\t\t}
\t\tif (pcie_bhi_addr != 0 || pcie_bhi_size != 0) {
\t\t\tprintf("pcie: stage: bhi window overridden to addr 0x%x size 0x%x\\n",
\t\t\t    pcie_bhi_addr, pcie_bhi_size);
\t\t}
\t}
""")

open(F, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("patched ok")