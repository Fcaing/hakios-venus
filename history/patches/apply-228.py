import sys
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(p).read()
if "apply-228" in s:
    print("already applied")
    sys.exit(0)
anchor = "pcie: stage: the first 4 KiB of the SBL segment were zeroed"
i = s.find(anchor)
assert i >= 0, "anchor not found"
# insert after the closing brace of that apply-227 block: find the "\n\t}\n" that follows
j = s.find("\n\t}\n", i)
assert j > i, "block end not found"
insert = """
	/* apply-228: fill the whole SBL code segment with "b ." so that
	 * a successful jump lands in an infinite loop.
	 */
	{
		uint32_t fake = 0;
		if (PE_parse_boot_argn("pcie_fake_sbl", &fake, sizeof(fake)) && fake != 0) {
			uint32_t w;
			for (w = 0; w < 0x12604 / 4; w++) {
				*((uint32_t *)(pcie_dma + 0x2000) + w) = 0xEAFFFFFEu;
			}
			printf("pcie: stage: the SBL segment is now an infinite loop\\n");
		}
	}
"""
s2 = s[:j + 4] + insert + s[j + 4:]
open(p, "w").write(s2)
print("written")