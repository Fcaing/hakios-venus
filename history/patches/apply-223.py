import io
path = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(path, encoding="utf-8").read()
def sub1(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:70])
    s = s.replace(old, new, 1)

old = "\t\t\tif (pcie_bar == 21) {\n"
new = """\t\t\tif (pcie_bar == 21) {
\t\t\t\t/*
\t\t\t\t * apply-223: vendor msm_pcie_config_controller() programs N_FTS in
\t\t\t\t * PCIE20_ACK_F_ASPM_CTRL_REG (dbi + 0x70c) right after link training,
\t\t\t\t * and enables the link/msi interrupts in parf + 0x22c.  A 512 KiB BHI
\t\t\t\t * read gets through without N_FTS, but the PBL then has to move that
\t\t\t\t * image into its own DDR in many acknowledged bursts; if the ack
\t\t\t\t * window is not set those bursts can be dropped and the PBL never
\t\t\t\t * leaves its boot loader.  That is exactly what p210..p218 show.
\t\t\t\t */
\t\t\t\t{
\t\t\t\t\tuint32_t nfts = rd(dbi.base + 0x70c);
\t\t\t\t\tuint32_t mask = rd(parf.base + 0x22c);
\t\t\t\t\twr(dbi.base + 0x70c, nfts | (1u << 15));
\t\t\t\t\twr(parf.base + 0x22c, 0x7f80c202u);
\t\t\t\t\tprintf("pcie: 5:   21: ack/aspm 0x70c 0x%08x -> 0x%08x, int mask 0x22c 0x%08x -> 0x%08x\\n",
\t\t\t\t\t    nfts, rd(dbi.base + 0x70c), mask, rd(parf.base + 0x22c));
\t\t\t\t}
"""
sub1(old, new)
io.open(path, "w", encoding="utf-8").write(s)
print("ok, new size", len(s))