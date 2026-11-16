import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
anchor = '\t\t\t\twr(bar0.base + 0x12c, 0);\n\t\t\t\twr(bar0.base + 0x10c, (uint32_t)(pcie_dma_pa >> 32));\n'
assert s.count(anchor) == 1
add = """\t\t\t\t/* apply-175: the endpoint can only fetch the image once it is a
\t\t\t\t * bus master.  star's bhi_request() writes the same 0x6 into
\t\t\t\t * both the RC's and the endpoint's command register. */
\t\t\t\t{
\t\t\t\t\tuint32_t dcmd = rd(dbi.base + 0x4);
\t\t\t\t\tuint32_t ecmd = rd(conf.base + 0x4);
\t\t\t\t\twr(dbi.base + 0x4, (dcmd & 0xffff0000u) | ((dcmd & 0xffffu) | 0x6));
\t\t\t\t\twr(conf.base + 0x4, (ecmd & 0xffff0000u) | ((ecmd & 0xffffu) | 0x6));
\t\t\t\t\tprintf("pcie: 5:   21: bus master on: dbi 0x4 = 0x%08x, conf 0x4 = 0x%08x\\n",
\t\t\t\t\t       rd(dbi.base + 0x4), rd(conf.base + 0x4));
\t\t\t\t}
\t\t\t\tprintf("pcie: 5:   21: bar0 0x128 = 0x%08x (star wants 0)\\n", rd(bar0.base + 0x128));
""" + anchor
s = s.replace(anchor, add, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-175 applied")
