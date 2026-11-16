p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(p).read()

# Silence every printf inside hakios_pcie_dma_init(): p140 showed that a single
# printf there (before UFS) leaves the phone at a black screen.
start = s.index("void\nhakios_pcie_dma_init(void)")
end = s.index("void\nhakios_pcie_init(void)")
body = s[start:end]
import re
n = 0
out = []
lines = body.split("\n")
i = 0
while i < len(lines):
    ln = lines[i]
    if "printf(" in ln and not ln.strip().startswith("*") and not ln.strip().startswith("/*"):
        # comment out this statement up to the terminating ';'
        stmt = [ln]
        j = i
        while ";" not in lines[j] and j + 1 < len(lines):
            j += 1
            stmt.append(lines[j])
        out.append("\t\t\t/* apply-154: silent, see p140 */")
        out.append("\t\t\tif (0) {")
        for sl in stmt:
            out.append(sl)
        out.append("\t\t\t}")
        n += 1
        i = j + 1
        continue
    out.append(ln)
    i += 1
body2 = "\n".join(out)
s = s[:start] + body2 + s[end:]
open(p, "w").write(s)
print("silenced", n, "printf statements in dma_init")