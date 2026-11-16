import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

start_marker = "\t\t\t\t{\n\t\t\t\t\tuint32_t st = 0, i, seq;\n\t\t\t\t\tvm_offset_t vec;"
end_marker = "pcie_note(\"bhie 0x%08x; \", st);\n\t\t\t\t\t}\n\t\t\t\t}\n"
assert s.count(start_marker) == 1, s.count(start_marker)
assert s.count(end_marker) == 1, s.count(end_marker)
s = s.replace(start_marker, "\t\t\t\t#if 0 /* apply-210: BHI only; the BHIE table read back as zeros, and its empty vectors send PBL to address 0 */\n" + start_marker, 1)
s = s.replace(end_marker, end_marker + "\t\t\t\t#endif\n", 1)

old_poll = ("if (((st >> 30) == 2 && rd(bar0.base + 0x128) == 1) ||\n"
            "\t\t\t\t\t\t    (st >> 30) == 3) {")
new_poll = "if ((st >> 30) == 2 || (st >> 30) == 3) {"
assert s.count(old_poll) == 1, s.count(old_poll)
s = s.replace(old_poll, new_poll, 1)

io.open(p, "w", encoding="utf-8").write(s)
print("ok apply-210")