import io
p = "/mnt/c/Users/Administrator/Documents/deepseek-harness/default-workspace/venus-recon/apply250.py"
src = io.open("/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c", encoding="utf-8").read()
a1 = "\t\t\t\t/* apply-226: read the memory the PBL would have written the\n"
assert src.count(a1) == 1, src.count(a1)
src = src.replace(a1, "\t\t\t\t/* apply-250: this probe reads a host address that does not exist and\n"
                       "\t\t\t\t * takes the kernel down with an abort, so the BHIE transfer after\n"
                       "\t\t\t\t * it never ran.  p222 has answered its question; keep it out.\n"
                       "\t\t\t\t */\n#if 0\n" + a1)
a2 = "\t\t\t\t\t\tprintf(\"pcie: 5:   21: sbl memory could not be mapped\\n\");\n\t\t\t\t\t}\n\t\t\t\t}\n"
assert src.count(a2) == 1, src.count(a2)
src = src.replace(a2, a2 + "#endif\n")
io.open("/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c", "w", encoding="utf-8").write(src)
print("apply-250 done, size", len(src))