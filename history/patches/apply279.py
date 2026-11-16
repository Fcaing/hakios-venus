import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
src = io.open(p, encoding="utf-8").read()
anchor = '\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-264 before init: mh 0x%08x ee 0x%08x cfg 0x%08x ctrl 0x%08x\\n",'
assert src.count(anchor) == 1, src.count(anchor)
block = '''\t\t\t\t\t\t\t/* apply-279: a function that no driver ever put into d0
\t\t\t\t\t\t\t * may refuse every mhi state change.  the vendor's resume
\t\t\t\t\t\t\t * path does pci_set_power_state(d0) before mhi starts,
\t\t\t\t\t\t\t * and we have never touched the pm capability. */
\t\t\t\t\t\t\t{
\t\t\t\t\t\t\t\tuint32_t capp = rd(conf.base + 0x34) & 0xfcu;
\t\t\t\t\t\t\t\tuint32_t pmo = 0, kk;

\t\t\t\t\t\t\t\tfor (kk = 0; kk < 48 && capp; kk++) {
\t\t\t\t\t\t\t\t\tuint32_t hid = rd(conf.base + capp);

\t\t\t\t\t\t\t\t\tif ((hid & 0xffu) == 0x01u) {
\t\t\t\t\t\t\t\t\t\tpmo = capp;
\t\t\t\t\t\t\t\t\t\tbreak;
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t\tcapp = (hid >> 8) & 0xfcu;
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\tif (pmo != 0) {
\t\t\t\t\t\t\t\t\tuint32_t raw = rd(conf.base + pmo + 4);
\t\t\t\t\t\t\t\t\tuint32_t csr = raw & 0xffffu;

\t\t\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-279 pm cap 0x%02x pmcsr 0x%04x (state %u)\\n", pmo, csr, csr & 3u);
\t\t\t\t\t\t\t\t\tif ((csr & 3u) != 0) {
\t\t\t\t\t\t\t\t\t\twr(conf.base + pmo + 4, (raw & 0xffff0000u) | (csr & ~3u));
\t\t\t\t\t\t\t\t\t\tsleep_ms(20);
\t\t\t\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-279 pmcsr now 0x%04x (state %u)\\n",
\t\t\t\t\t\t\t\t\t\t    rd(conf.base + pmo + 4) & 0xffffu, rd(conf.base + pmo + 4) & 3u);
\t\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t\t} else {
\t\t\t\t\t\t\t\t\tprintf("pcie: 5:   21: apply-279 no pm capability at 0x%08x\\n", rd(conf.base + 0x34));
\t\t\t\t\t\t\t\t}
\t\t\t\t\t\t\t}
'''
src = src.replace(anchor, block + anchor, 1)
io.open(p, "w", encoding="utf-8").write(src)
print("apply-279 applied")