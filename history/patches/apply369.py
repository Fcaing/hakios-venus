P = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(P).read()

old = "\t\t\t\t\twr(pcie_dma_extra + 0x2400 + 0x0c, (uint32_t)cbase);\n"
assert s.count(old) == 1, s.count(old)
new = (
    "\t\t\t\t\t/* apply-369: the command ring context was left with type 0, the\n"
    "\t\t\t\t\t * event ring has type 1.  A type of 0 is not a ring, so the\n"
    "\t\t\t\t\t * device may never start the command engine at all. */\n"
    "\t\t\t\t\twr(pcie_dma_extra + 0x2400 + 0x00, 0u);\n"
    "\t\t\t\t\twr(pcie_dma_extra + 0x2400 + 0x04, 1u);\n"
    "\t\t\t\t\twr(pcie_dma_extra + 0x2400 + 0x08, 0u);\n"
    + old
)
s = s.replace(old, new)
open(P, "w").write(s)
print("apply-369 ok")
