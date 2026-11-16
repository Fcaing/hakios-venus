import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
assert "apply-334" not in s
T = "\t" * 9

a = T + "\twr(bar0.base + 0x224 + 0x64, (uint32_t)(rtab >> 32));"
assert s.count(a) == 1
pre = (T + "\t/* apply-334: the vendor clears the BHIE receive registers first, their\n"
       + T + "\t * power-on values are undefined. */\n"
       + T + "\tfor (rw = 0; rw < 8u; rw++) {\n"
       + T + "\t\twr(bar0.base + 0x224 + 0x60 + rw * 4u, 0);\n"
       + T + "\t}\n")
s = s.replace(a, pre + a, 1)

b = T + "\twr(bar0.base + 0x38, (rd(bar0.base + 0x38) & ~0xff00u) | (2u << 8));\n" + T + "\tsleep_ms(400);\n"
assert s.count(b) == 1, s.count(b)
newb = (T + "\t/* apply-334: the vendor forces rddm by asking for the sys_err state,\n"
        + T + "\t * then waits for the execution environment to become rddm. */\n"
        + T + "\twr(bar0.base + 0x38, 0xff00u);\n"
        + T + "\tfor (rw = 0; rw < 20u; rw++) {\n"
        + T + "\t\tsleep_ms(150);\n"
        + T + "\t\tif ((rw % 4u) == 0u) {\n"
        + T + "\t\t\tprintf(\"apply-334 t=%u ms mh %08x ee %08x rxst %08x\\n\",\n"
        + T + "\t\t\t    rw * 150u, rd(bar0.base + 0x48), rd(bar0.base + 0x128), rd(bar0.base + 0x224 + 0x78));\n"
        + T + "\t\t}\n"
        + T + "\t}\n")
s = s.replace(b, newb, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-334 ok")