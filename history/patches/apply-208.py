import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

anchor = 'printf("pcie: 2:   the port is powered\\n");'
assert s.count(anchor) == 1, s.count(anchor)

block = r'''	/* apply-208: gcc_aggre_noc_pcie_0_axi_clk (gcc-lahaina.c:1812) is enabled
	 * through GCC_VOTE_0 bit 12.  vote0 read 0x00ec0d7f on p203: pcie_1's axi
	 * clock (bit 11) was on, pcie_0's (bit 12) was not.  The BHI doorbell is
	 * an AXI access from the endpoint into DDR, so a halted aggre-noc path
	 * would swallow it before the SMMU ever sees it. */
	{
		uint32_t vote0 = rd(gcc.base + GCC_VOTE_0);
		if (!(vote0 & (1u << 12))) {
			wr(gcc.base + GCC_VOTE_0, vote0 | (1u << 12));
			printf("pcie: 2:   aggre noc pcie0 axi was off: vote0 0x%08x -> 0x%08x\n",
			    vote0, rd(gcc.base + GCC_VOTE_0));
		} else {
			printf("pcie: 2:   aggre noc pcie0 axi already on: vote0 0x%08x\n", vote0);
		}
	}
'''
s = s.replace(anchor, block + anchor, 1)
io.open(p, "w", encoding="utf-8").write(s)
print("ok apply-208")