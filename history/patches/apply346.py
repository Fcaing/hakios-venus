import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
old = "if (pcie_mhi_data != 0 && smmu_state == 1) {"
n = s.count(old)
print("data gates", n)
assert n == 2, n
# 只关掉后面的那个（数据实验块），保留前面那个较早的同名判断
i = s.rfind(old)
s = s[:i] + "if (0) { /* apply-346: the data block is compiled out */" + s[i+len(old):]
io.open(p, "w", encoding="utf-8").write(s)
print("patched")