import io
import sys

p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
orig = s


def sub1(old, new, what):
    global s
    if s.count(old) != 1:
        print("FAIL %s: count=%d" % (what, s.count(old)))
        sys.exit(1)
    s = s.replace(old, new, 1)
    print("ok %s" % what)


anchor = """						pcie_note("bhie 0x%08x; ", st);
					}
				}
"""
probe = """						pcie_note("bhie 0x%08x; ", st);
					}
				}
				/*
				 * apply-205: does the endpoint drive these registers, or
				 * are they ordinary memory that holds whatever we write?
				 *
				 * BHI_STATUS reads back what we put in it => nobody is
				 * polling it.  It reads zero right after a write => the
				 * PBL is alive and clearing it, and the doorbell is what
				 * it is not looking at.  Same question for MHICTRL.
				 */
				if (smmu_state == 1 && pcie_dma_pa != 0) {
					uint32_t	was, r1, r2, r3;

					was = rd(bar0.base + 0x12c);
					wr(bar0.base + 0x12c, 0x80000000u);
					r1 = rd(bar0.base + 0x12c);
					wr(bar0.base + 0x12c, 0x40000000u);
					r2 = rd(bar0.base + 0x12c);
					wr(bar0.base + 0x12c, 0);
					r3 = rd(bar0.base + 0x12c);
					printf("pcie: 5:   21: status writability: was 0x%08x, 0x80000000 read 0x%08x, 0x40000000 read 0x%08x, 0 read 0x%08x\\n",
					       was, r1, r2, r3);
					pcie_note("status was 0x%08x r1 0x%08x r2 0x%08x r3 0x%08x; ",
					    was, r1, r2, r3);

					was = rd(bar0.base + 0x38);
					wr(bar0.base + 0x38, was | 0x2u);
					r1 = rd(bar0.base + 0x38);
					wr(bar0.base + 0x38, was);
					r2 = rd(bar0.base + 0x38);
					printf("pcie: 5:   21: mhictrl writability: was 0x%08x, reset set read 0x%08x, restored read 0x%08x\\n",
					       was, r1, r2);
				}
"""
sub1(anchor, probe, "probe block")

if s == orig:
    print("FAIL nothing changed")
    sys.exit(1)

io.open(p, "w", encoding="utf-8").write(s)
print("written")
