#!/usr/bin/env python3
"""apply-422: list every entry the command DB carries.

The two things cnss2 does that we have never done are (a) an interconnect bandwidth vote on
pcie_to_memnoc / memnoc_to_ddr and (b) an RPMh TCS command for the internal PA supply
(qcom,tcs_offset_int_pow_amp_vreg = 0x4d0).  Before writing either, read out the whole command
DB and see which bus resources actually exist on this part.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
END = "\t/* apply-169: back to the loader at the end of the probe, so the log is readable. */\n"

BLOCK = r'''	/* apply-422: what bus resources does the command DB carry? */
	if (pcie_mhi_data == 42u) {
		printf("apply-422 cmd-db dump follows\n");
		cmddb_dump();
		printf("apply-422 done\n");
	}

'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(END) == 1, "end marker"
assert "apply-422" not in src

a1 = "pcie_mhi_data != 41u && pcie_chanstart != 0"
a2 = "pcie_mhi_data != 41u) wr(pcie_dma_extra + 20 * 0x2c"
assert src.count(a1) == 1 and src.count(a2) == 1, "gate anchors"
src = src.replace(a1, "pcie_mhi_data != 41u && pcie_mhi_data != 42u && pcie_chanstart != 0")
src = src.replace(a2, "pcie_mhi_data != 41u && pcie_mhi_data != 42u) wr(pcie_dma_extra + 20 * 0x2c")

a = src.index(END)
src = src[:a] + BLOCK + src[a:]
assert src.count("apply-422 done") == 1
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-422 ok")
