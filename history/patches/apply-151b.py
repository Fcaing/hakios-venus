p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = open(p).read()
lines = s.split("\n")
out = []
done = False
for ln in lines:
    if not done and ln.startswith("static vm_offset_t pcie_dma;"):
        out.append("static vm_offset_t pcie_dma;")
        out.append("static uint32_t pcie_dma_size = PCIE_DMA_SIZE;")
        done = True
        continue
    out.append(ln)
assert done
s = "\n".join(out)
# declare the constant right after the includes block: put it before the first "static uint32_t pcie_only"
anchor = "static uint32_t pcie_only"
i = s.index(anchor)
decl = ("/* apply-151: the DMA page is 512 KiB, the unit star's BHI upload uses (WIFI_DMA_SIZE 0x80000);\n"
        " * it is taken in hakios_pcie_dma_init(), before UFS, because nothing may allocate at\n"
        " * hakios_pcie_init() time. */\n"
        "#define PCIE_DMA_SIZE 0x80000u\n")
s = s[:i] + decl + s[i:]
open(p, "w").write(s)
print("done")