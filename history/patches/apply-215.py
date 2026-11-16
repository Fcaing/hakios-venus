import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

# 1) 把 apply-205 的可写性测试包掉：它会写 0x12c，把 PBL 刚写下的 SUCCESS 冲掉
old205 = "\t\t\t\tif (smmu_state == 1 && pcie_dma_pa != 0) {\n\t\t\t\t\tuint32_t\twas, r1, r2, r3;"
assert s.count(old205) == 1, s.count(old205)
s = s.replace(old205,
    "\t\t\t\t/* apply-215: this probe wrote 0x12c and wiped the SUCCESS the PBL had\n"
    "\t\t\t\t * just left there, which is why p210 printed status 0 while its own\n"
    "\t\t\t\t * window dump showed 0x82dc6454. It has done its job; keep it out. */\n"
    "\t\t\t\t#if 0\n" + old205, 1)

old205_end = "\t\t\t\t\tprintf(\"pcie: 5:   21: mhictrl writability: was 0x%08x, reset set read 0x%08x, restored read 0x%08x\\n\",\n\t\t\t\t\t       was, r1, r2);\n\t\t\t\t}"
assert s.count(old205_end) == 1, s.count(old205_end)
s = s.replace(old205_end, old205_end + "\n\t\t\t\t#endif", 1)

# 2) 轮询结束后补一行：多少次之后看到的状态（不写寄存器）
oldpoll = """				{
					uint32_t i;

					for (i = 0; i < 100; i++) {
						uint32_t st = rd(bar0.base + 0x12c);

						if ((st >> 30) == 2 || (st >> 30) == 3) {
							break;
						}
						sleep_ms(100);
					}
				}"""
assert s.count(oldpoll) == 1, s.count(oldpoll)
newpoll = """				{
					uint32_t i;

					for (i = 0; i < 100; i++) {
						uint32_t st = rd(bar0.base + 0x12c);

						if ((st >> 30) == 2 || (st >> 30) == 3) {
							break;
						}
						sleep_ms(100);
					}
					printf("pcie: 5:   21: bhi polls %u, status 0x%08x, mhi status 0x%08x (ready %u state %u)\\n",
					    i, rd(bar0.base + 0x12c), rd(bar0.base + 0x48),
					    rd(bar0.base + 0x48) & 1u, (rd(bar0.base + 0x48) >> 8) & 0xffu);
				}"""
s = s.replace(oldpoll, newpoll, 1)

io.open(p, "w", encoding="utf-8").write(s)
print("ok apply-215")