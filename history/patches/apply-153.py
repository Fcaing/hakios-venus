p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(p).read()
old = '''\tif (pcie_dma != 0 || !PE_parse_boot_argn("pcie", &wants, sizeof(wants)) || wants == 0) {
\t\treturn;
\t}'''
new = '''\tif (pcie_dma != 0 || !PE_parse_boot_argn("pcie", &wants, sizeof(wants)) || wants == 0) {
\t\treturn;
\t}
\t/* apply-153: pcie_dma_skip=1 takes nothing, to test whether the allocation
\t * itself (and not the pcie code that follows) is what hangs the boot. */
\t{
\t\tuint32_t skip = 0;
\t\tif (PE_parse_boot_argn("pcie_dma_skip", &skip, sizeof(skip)) && skip != 0) {
\t\t\tprintf("pcie: dma init: skipped on request\\n");
\t\t\treturn;
\t\t}
\t}'''
assert s.count(old) == 1
s = s.replace(old, new)
open(p, "w").write(s)
print("apply-153 written")