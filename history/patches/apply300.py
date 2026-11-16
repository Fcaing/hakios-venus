import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
old = "wr(bar0.base + 0x300 + 20 * 8, (uint32_t)trewp);"
assert s.count(old) == 1, s.count(old)
new = ("/* apply-300: the vendor writes the doorbell as two 32-bit halves:\n"
       "\t\t\t\t\t\t * high half to db_addr + 4 first, then the low half.\n"
       "\t\t\t\t\t\t * We only ever wrote the low half. */\n"
       "\t\t\t\t\t\twr(bar0.base + 0x300 + 20 * 8 + 4u, 0u);\n"
       "\t\t\t\t\t\t" + old)
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("patched")