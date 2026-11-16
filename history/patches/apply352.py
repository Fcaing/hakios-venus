import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old1 = "static uint32_t pcie_qmi;"
assert s.count(old1) == 1
s = s.replace(old1, old1 + "\nstatic uint32_t pcie_qmi_len = 0x34; /* apply-352: the vendor sends 0x34 bytes, not a whole page */")

old2 = "\t\t\t\t\t\tif (0) { /* apply-346: the data block is compiled out */"
assert s.count(old2) == 1
s = s.replace(old2, "\t\t\t\t\t\tif (pcie_qmi != 0) { /* apply-352: send the qmi packet as the first tre */")

old3 = """							printf("apply-335 d: flushed\\n");
"""
assert s.count(old3) == 1
new3 = """							printf("apply-335 d: flushed\\n");
							{
								uint32_t ql = pcie_qmi_len;

								if (PE_parse_boot_argn("pcie_qmi_len", &ql, sizeof(ql))) {
									pcie_qmi_len = ql;
								}
								wr(pcie_dma_extra + dring_off + 0x0008, pcie_qmi_len);
								wr(pcie_dma_extra + dring_off + 0x0018, pcie_qmi_len);
								printf("apply-352 tre len now 0x%08x (packet 51 bytes)\\n",
								    rd(pcie_dma_extra + dring_off + 0x0008));
							}
"""
s = s.replace(old3, new3)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-352 ok")