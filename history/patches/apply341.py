import io
p="/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s=io.open(p,encoding="utf-8").read()

# revert apply-338 gate
old338=("\t\t\t\t\t\tif (pcie_rp_fix != 0) {\n"
        "\t\t\t\t\t\t\twr(pcie_dma_extra + dch * 0x2c + 0x1c, (uint32_t)(dring));\n"
        "\t\t\t\t\t\t\twr(pcie_dma_extra + dch * 0x2c + 0x20, 0u);\n"
        "\t\t\t\t\t\t}\n")
assert s.count(old338)==1
s=s.replace(old338,("\t\t\t\t\t\twr(pcie_dma_extra + dch * 0x2c + 0x1c, (uint32_t)(dring));\n"
                    "\t\t\t\t\t\twr(pcie_dma_extra + dch * 0x2c + 0x20, 0u);\n"),1)

# revert apply-339 delay
old339=("\t\t\t\t\t\tif (pcie_m0_delay != 0) {\n"
        "\t\t\t\t\t\t\tsleep_ms(pcie_m0_delay);\n"
        "\t\t\t\t\t\t}\n")
assert s.count(old339)==1
s=s.replace(old339,"",1)
io.open(p,"w",encoding="utf-8").write(s)
print("apply-341 reverted 338/339 changes")