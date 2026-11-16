import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
L = io.open(p, encoding="utf-8").read().split("\n")
# 定位块边界：apply-332 注释行 到 apply-333 hits 打印行；apply-335 enter 到其块尾
def find(sub, start=0):
    for i in range(start, len(L)):
        if sub in L[i]:
            return i
    raise SystemExit("not found: " + sub)
a = find("apply-332: build the RDDM receive table")
b = find("apply-333 hits %u", a)
c = find("apply-335 enter, mh 0x%08x va 0x%llx")
d = find("apply-335 e: tre at 0x%llx keeps len %u", c)
print("blocks", a, b, c, d)
# 从注释行的上一行（if (pcie_rddm != 0) {）开始关，避免残留半截
a0 = a
while "if (pcie_rddm" not in L[a0]:
    a0 -= 1
print("rddm gate at", a0 + 1, L[a0].strip())
L[a0] = L[a0].replace("if (pcie_rddm != 0) {", "if (0) { /* apply-345: rddm blocks compiled out */")
L.insert(a0 + 1, "")
io.open(p, "w", encoding="utf-8").write("\n".join(L))
print("gate neutralised; source", len("\n".join(L)))