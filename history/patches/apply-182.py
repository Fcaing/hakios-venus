import io

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()

old = """					if (ctrl & 2u) {
						wr(bar0.base + 0x38, ctrl & ~2u);
						sleep_ms(20);
						printf("pcie: 5:   21: mhi reset cleared: 0x%08x -> 0x%08x\\n",
						       ctrl, rd(bar0.base + 0x38));
					}"""
new = """					if (ctrl & 2u) {
						wr(bar0.base + 0x38, ctrl & ~2u);
						sleep_ms(20);
						printf("pcie: 5:   21: mhi reset cleared: 0x%08x -> 0x%08x\\n",
						       ctrl, rd(bar0.base + 0x38));
					}
					/*
					 * apply-182: p183 proved every BHI register really takes
					 * the value written (addr, size, doorbell 1), yet the
					 * device answers nothing at all: status stays RESET and
					 * no DMA ever reaches the SMMU.  Pulse the MHI reset so
					 * the endpoint's MHI/BHI state machine starts from a
					 * known state before the image is offered again.
					 */
					wr(bar0.base + 0x38, 2u);
					sleep_ms(20);
					wr(bar0.base + 0x38, 0u);
					sleep_ms(20);
					printf("pcie: 5:   21: mhi after the reset pulse: ctrl 0x%08x status 0x%08x\\n",
					       rd(bar0.base + 0x38), rd(bar0.base + 0x48));"""
assert s.count(old) == 1, s.count(old)
s = s.replace(old, new)

io.open(p, "w", encoding="utf-8").write(s)
print("patched")