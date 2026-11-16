import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
old = '''\t\t\t\t\t\tPE_parse_boot_argn("pcie_mhi_init", &want, sizeof(want));
\t\t\t\t\t\tPE_parse_boot_argn("pcie_chanstart", &want, sizeof(want));
\t\t\t\t\t\tpcie_chanstart = want;'''
assert s.count(old) == 1, s.count(old)
new = '''\t\t\t\t\t\t/*
\t\t\t\t\t\t * apply-285: pcie_chanstart used to be parsed into the same
\t\t\t\t\t\t * variable as pcie_mhi_init, so "pcie_chanstart=0" switched the
\t\t\t\t\t\t * whole mhi bring-up off.  Keep them apart.
\t\t\t\t\t\t */
\t\t\t\t\t\t{
\t\t\t\t\t\t\tuint32_t wcs = pcie_chanstart;

\t\t\t\t\t\t\tPE_parse_boot_argn("pcie_mhi_init", &want, sizeof(want));
\t\t\t\t\t\t\tif (PE_parse_boot_argn("pcie_chanstart", &wcs, sizeof(wcs))) {
\t\t\t\t\t\t\t\tpcie_chanstart = wcs;
\t\t\t\t\t\t\t}
\t\t\t\t\t\t}'''
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-285: chanstart no longer clobbers mhi_init")