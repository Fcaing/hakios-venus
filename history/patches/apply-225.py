import io
path = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(path, encoding="utf-8").read()
def sub1(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:100])
    s = s.replace(old, new, 1)

sub1("for (k = 0; k < 150; k++) {", "for (k = 0; k < 30; k++) {")
sub1("if (k == 20 || k == 60 || k == 120) {", "if (k == 5 || k == 15 || k == 29) {")

old = """						printf("pcie: 5:   21: mhi ready after %u polls: status 0x%08x (ready %u state %u) ee 0x%08x\\n",
						    k, rd(bar0.base + 0x48), rd(bar0.base + 0x48) & 1u,
						    (rd(bar0.base + 0x48) >> 8) & 0xffu, rd(bar0.base + 0x128));
"""
new = """						printf("pcie: 5:   21: apply-225 final: fw size 0x%llx, bhi[0x108] 0x%08x bhi[0x110] 0x%08x bhi[0x12c] 0x%08x ee 0x%08x mhistatus 0x%08x (ready %u state %u) after %u x 100 ms\\n",
						    (unsigned long long)pcie_fw_size,
						    rd(bar0.base + 0x108), rd(bar0.base + 0x110),
						    rd(bar0.base + 0x12c), rd(bar0.base + 0x128),
						    rd(bar0.base + 0x48), rd(bar0.base + 0x48) & 1u,
						    (rd(bar0.base + 0x48) >> 8) & 0xffu, k);
"""
sub1(old, new)
io.open(path, "w", encoding="utf-8").write(s)
print("ok", len(s))