# -*- coding: utf-8 -*-
import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

# 1) new boot arg declaration
a1 = "static uint32_t pcie_mhi_data;\t/* apply-292: push one data tre at the ipcr tx channel */"
assert s.count(a1) == 1
s = s.replace(a1, a1 + "\nstatic uint32_t pcie_chanlate;\t/* apply-309: write the channel contexts in mission mode only */")

# 2) gate the SBL-time channel context loop
a2 = "\t\t\t\t\t\t\t\t\tstatic const uint32_t chans[6] = { 0, 1, 4, 5, 20, 21 };\n"
assert s.count(a2) == 1
s = s.replace(a2, "\t\t\t\t\t\t\t\t\tstatic const uint32_t chans[6] = { 0, 1, 4, 5, 20, 21 };\n\n\t\t\t\t\t\t\t\t\t/* apply-309: the vendor writes these only after the\n\t\t\t\t\t\t\t\t\t * device is in mission mode. */\n\t\t\t\t\t\t\t\t\tif (pcie_chanlate == 0) {\n")

a3 = "\t\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x28, (uint32_t)(rb >> 32));\n\t\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t\t}\n"
assert s.count(a3) == 1
s = s.replace(a3, "\t\t\t\t\t\t\t\t\t\twr(pcie_dma_extra + o3 + 0x28, (uint32_t)(rb >> 32));\n\t\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t\t}\n")

# 3) parse the boot arg next to pcie_mhi_data's parse
a4 = "if (PE_parse_boot_argn(\"pcie_mhi_data\", &d2, sizeof(d2))) {\n"
assert s.count(a4) == 1
s = s.replace(a4, "if (PE_parse_boot_argn(\"pcie_chanlate\", &d2, sizeof(d2))) {\n\t\t\t\t\t\t\t\t\tpcie_chanlate = d2;\n\t\t\t\t\t\t\t\t}\n\t\t\t\t\t\t\t\td2 = 0;\n\t\t\t\t\t\t\t\t" + a4.strip() + "\n")

# 4) apply-308 must not wipe the er/cmd contexts anymore
a5 = "\t\t\t\t\t\tfor (i8 = 0; i8 < 0x2000; i8 += 4) {\n"
if s.count(a5) == 0:
    a5 = "\t\t\t\t\t\tfor (i8 = 0x2000; i8 < 0x2480; i8 += 4) {\n\t\t\t\t\t\t\twr(pcie_dma_extra + i8, 0);\n\t\t\t\t\t\t}\n"
    assert s.count(a5) == 1, s.count(a5)
    s = s.replace(a5, "")
a6 = "\t\t\t\t\t\tfor (i8 = 0; i8 < 3; i8++) {\n\t\t\t\t\t\t\to8 = 0x2000 + i8 * 0x2c;\n"
assert s.count(a6) == 1
start = s.index(a6)
end = s.index("\t\t\t\t\t\t{\n\t\t\t\t\t\t\tstatic const uint32_t chans8[6]", start)
s = s[:start] + s[end:]
io.open(p, "w", encoding="utf-8").write(s)
print("apply-309 applied")