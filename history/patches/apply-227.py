import sys
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(p).read()
if "apply-227" in s:
    print("already applied")
    sys.exit(0)
anchor = "pcie_dma_staged = 1;"
i = s.find(anchor)
assert i >= 0, "anchor not found"
j = s.find("\n", i)
assert j > i
insert = """
	/* apply-227: zero the first 4 KiB of the SBL code segment while
	 * leaving the ELF header and the program headers untouched, to see
	 * whether the PBL validates the payload or only the header.
	 */
	{
		uint32_t corrupt = 0;
		if (PE_parse_boot_argn("pcie_corrupt_seg2", &corrupt, sizeof(corrupt)) && corrupt != 0) {
			memset((void *)(pcie_dma + 0x2000), 0, 4096);
			printf("pcie: stage: the first 4 KiB of the SBL segment were zeroed\\n");
		}
	}
"""
s2 = s[:j + 1] + insert + s[j + 1:]
open(p, "w").write(s2)
print("written")