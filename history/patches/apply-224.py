import io
path = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(path, encoding="utf-8").read()
def sub1(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:80])
    s = s.replace(old, new, 1)

old = """				wr(bar0.base + 0x10c, 0u);
				/* apply-209: the BHI doorbell used 0xa0000000, which the SMMU does not
				 * map (only 0xa0004000.. is in the page tables), so p204 got
				 * FSR 0x80000402 on every fetch.  Point it at the mapped window. */
				wr(bar0.base + 0x108, (uint32_t)PCIE_SMMU_IOVA);
				wr(bar0.base + 0x110, PCIE_DMA_SIZE);
"""
new = """				/*
				 * apply-224: hand the PBL the whole image, not just the 512 KiB
				 * staging page.  amss.bin is 5,236,304 bytes and its 8th PT_LOAD
				 * runs from file offset 0x31000 to 0x165000 (1.2 MiB), so a PBL
				 * that only loaded the first 512 KiB would jump into SBL and
				 * execute straight off the end of the loaded region.  The 8 MiB
				 * region at 0xa0200000 is already mapped in the SMMU page tables
				 * and already holds the whole image at +0x20000, so point the
				 * doorbell there and tell it the real size.
				 */
				wr(bar0.base + 0x10c,
				    (uint32_t)((PCIE_EXTRA_IOVA + PCIE_EXTRA_DATA_OFF) >> 32));
				wr(bar0.base + 0x108,
				    (uint32_t)(PCIE_EXTRA_IOVA + PCIE_EXTRA_DATA_OFF));
				wr(bar0.base + 0x110, (uint32_t)pcie_fw_size);
				printf("pcie: 5:   21: apply-224: bhi gets the whole image: addr 0x%llx size 0x%llx\\n",
				    (unsigned long long)(PCIE_EXTRA_IOVA + PCIE_EXTRA_DATA_OFF),
				    (unsigned long long)pcie_fw_size);
"""
sub1(old, new)
io.open(path, "w", encoding="utf-8").write(s)
print("ok", len(s))