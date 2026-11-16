#!/usr/bin/env python3
"""apply-410: fix the pointer truncation in apply-409 (it panicked the kernel).

apply-409 did `uint32_t cbase = pcie_dma_extra + 0x2000u + e409 * 0x2cu;` -- that truncates
the 64-bit mapping to 32 bits, and the first rd() on it was a kernel data abort:

    panic(cpu 0 caller ...): Kernel data abort. at pc 0xfffffff0074c9ff8
    cpu_signal failed in DebuggerXCallEnter (x3)
    ... right after "apply-409 a: cfg 0x00030880 ..."

Same trap as apply-386/387.  Keep the offset in a uint32_t and add pcie_dma_extra at the
point of use.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()

old = "\t\t\tuint32_t cbase = pcie_dma_extra + 0x2000u + e409 * 0x2cu;\n\t\t\tuint32_t rb = rd(cbase + 0x0cu);\n"
assert src.count(old) == 1, "anchor"

new = ("\t\t\tuint32_t cofs410 = 0x2000u + e409 * 0x2cu;\t/* apply-410: offset, not a pointer */\n"
       "\t\t\tuint32_t rb = rd(pcie_dma_extra + cofs410 + 0x0cu);\n")
src = src.replace(old, new)

a = "rd(cbase)"
assert src.count(a) == 1, "cbase bare"
src = src.replace(a, "rd(pcie_dma_extra + cofs410)")

# every other cbase use in that block
for off in ("0x08u", "0x14u", "0x1cu", "0x24u"):
    a = "rd(cbase + %s)" % off
    assert src.count(a) == 1, "cbase use %s" % off
    src = src.replace(a, "rd(pcie_dma_extra + cofs410 + %s)" % off)

assert "pcie_dma_extra + 0x2000u + e409" not in src
assert "rd(cbase" not in src
src = src.replace("apply-409 a:", "apply-410 a:").replace("apply-409 b:", "apply-410 b:")
src = src.replace("apply-409 c:", "apply-410 c:").replace("apply-409 d:", "apply-410 d:")
src = src.replace("apply-409 e:", "apply-410 e:").replace("apply-409 f:", "apply-410 f:")
assert "apply-410 a:" in src
src = src.replace("/* apply-409: every event ring", "/* apply-410: every event ring")
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-410 ok")
