import sys
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(p).read()
if "apply-226" in s:
    print("already applied")
    sys.exit(0)
anchor = 'printf("pcie: 5:   21: apply-225 final:'
i = s.find(anchor)
assert i >= 0, "anchor not found"
j = s.find(";", i)
assert j > i, "no semicolon"
insert = """
				/* apply-226: read the memory the PBL would have written the
				 * SBL segments into, to tell "PBL read but could not write
				 * DDR" from "SBL ran and fell over".
				 */
				{
					vm_offset_t probe = ml_io_map_unmappable(0x1426000, 0x1c000, VM_WIMG_IO);
					uint32_t k;
					if (probe != 0) {
						printf("pcie: 5:   21: sbl memory 0x1427000: ");
						for (k = 0; k < 8; k++)
							printf("%08x ", rd(probe + 0x1000 + k * 4));
						printf("\\n");
						printf("pcie: 5:   21: sbl entry 0x1439500: ");
						for (k = 0; k < 8; k++)
							printf("%08x ", rd(probe + (0x1439500 - 0x1426000) + k * 4));
						printf("\\n");
					} else {
						printf("pcie: 5:   21: sbl memory could not be mapped\\n");
					}
				}
"""
s2 = s[:j + 1] + insert + s[j + 1:]
open(p, "w").write(s2)
print("written, inserted at line", s[:j].count("\n") + 1)