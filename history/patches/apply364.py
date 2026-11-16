P = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
src = open(P).read()


def dump_code(tag):
    return """
						{	/* apply-364: raw context words, so we can see what the device
							 * actually wrote and at which offset. */
							uint32_t o4;

							printf("pcie: 5:   21: apply-364 %s er ctx raw:");
							for (o4 = 0; o4 < 0x60; o4 += 4) {
								printf(" %%08x", rd(pcie_dma_extra + 0x2000 + o4));
							}
							printf("\\n");
							printf("pcie: 5:   21: apply-364 %s cmd ctx raw:");
							for (o4 = 0; o4 < 0x30; o4 += 4) {
								printf(" %%08x", rd(pcie_dma_extra + 0x2400 + o4));
							}
							printf("\\n");
						}
""" % (tag, tag)


a = '\t\t\t\t\tprintf("pcie: 5:   21: apply-286 m0 after mission: mh 0x%08x ee 0x%08x ctrl 0x%08x\\n",'
assert src.count(a) == 1, ("a", src.count(a))
i = src.index(a)
j = src.index("\n", src.index(");", i)) + 1
src = src[:j] + dump_code("a") + src[j:]

b = '\t\t\t\t\t\tprintf("pcie: 5:   21: apply-282 chstart tre %08x %08x %08x %08x cc wp 0x%08x mh 0x%08x ee 0x%08x\\n",'
assert src.count(b) == 1, ("b", src.count(b))
i = src.index(b)
src = src[:i] + dump_code("b") + src[i:]

open(P, "w").write(src)
print("apply-364 ok")
