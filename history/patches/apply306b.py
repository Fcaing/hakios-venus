import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

head = '''uint32_t dch = pcie_data_ch;
						uint32_t didx = (dch == 0u) ? 0u : (dch == 1u) ? 1u : (dch == 4u) ? 2u : (dch == 5u) ? 3u : (dch == 20u) ? 4u : 5u;
						uint32_t dring_off = 0x8000u + didx * 0x1000u;
						uint64_t dring = PCIE_EXTRA_IOVA + dring_off;
'''
assert s.count(head) == 1, ("head", s.count(head))
s = s.replace(head, "", 1)

anchor = "uint64_t datiova = PCIE_EXTRA_IOVA + 0x3000;"
assert s.count(anchor) == 1, ("anchor", s.count(anchor))
s = s.replace(anchor, head + "\t\t\t\t\t\t" + anchor, 1)

io.open(p, "w", encoding="utf-8").write(s)
print("declaration moved before its first use")