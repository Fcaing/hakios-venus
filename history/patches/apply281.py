import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

# 1) 把 apply-280 的打印重复一份到 apply-225 final 之前（日志尾部，不会被 GPU 刷屏挤掉）
anchor = '\t\t\t\t\tprintf("pcie: 5:   21: apply-225 final: fw size 0x%llx'
assert s.count(anchor) == 1, s.count(anchor)
add = ('\t\t\t\t\tif (pcie_mhi_m0late != 0) {\n'
       '\t\t\t\t\t\tprintf("pcie: 5:   21: apply-280 tail: mh 0x%08x ee 0x%08x ctrl 0x%08x ch20 rp 0x%08x wp 0x%08x\\n",\n'
       '\t\t\t\t\t\t    rd(bar0.base + 0x48), rd(bar0.base + 0x128), rd(bar0.base + 0x38),\n'
       '\t\t\t\t\t\t    rd(pcie_dma_extra + 20u * 0x2cu + 0x1cu), rd(pcie_dma_extra + 20u * 0x2cu + 0x24u));\n'
       '\t\t\t\t\t}\n')
s = s.replace(anchor, add + anchor)
io.open(p, "w", encoding="utf-8").write(s)
print("apply-281 tail print inserted")