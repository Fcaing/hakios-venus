import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
# retarget RDDM away from the firmware image copy (which spans 0xa0220000..0xa071fa50)
s = s.replace("uint64_t rtab = PCIE_EXTRA_IOVA + 0x620000ull;",
              "uint64_t rtab = PCIE_EXTRA_IOVA + 0x790000ull;")
s = s.replace("for (rseg = 0; rseg < 9u; rseg++) {", "for (rseg = 0; rseg < 5u; rseg++) {")
s = s.replace("uint64_t sa = PCIE_EXTRA_IOVA + 0x200000ull + (uint64_t)rseg * 0x80000ull;",
              "uint64_t sa = PCIE_EXTRA_IOVA + 0x520000ull + (uint64_t)rseg * 0x80000ull;")
s = s.replace("uint64_t sl = (rseg == 8u) ? 0x20000ull : 0x80000ull;", "uint64_t sl = 0x80000ull;")
# table entries and writes: switch offsets 0x620000 -> 0x790000
s = s.replace("pcie_dma_extra + 0x620000", "pcie_dma_extra + 0x790000")
s = s.replace("wr(pcie_dma_extra + 0x790000 + 144u", "wr(pcie_dma_extra + 0x790000 + 80u")
s = s.replace("wr(pcie_dma_extra + 0x790000 + 148u", "wr(pcie_dma_extra + 0x790000 + 84u")
s = s.replace("wr(pcie_dma_extra + 0x790000 + 152u, 160u);", "wr(pcie_dma_extra + 0x790000 + 88u, 96u);")
s = s.replace("wr(pcie_dma_extra + 0x790000 + 156u, 0);", "wr(pcie_dma_extra + 0x790000 + 92u, 0);")
s = s.replace("wr(bar0.base + 0x224 + 0x68, 160u);", "wr(bar0.base + 0x224 + 0x68, 96u);")
# reading back: seg0 lives at 0x520000 now
s = s.replace("pcie_dma_extra + 0x200000 + rw", "pcie_dma_extra + 0x520000 + rw")
s = s.replace("pcie_dma_extra + 0x200000u + sg2 * 0x80000u", "pcie_dma_extra + 0x520000u + sg2 * 0x80000u")
s = s.replace("for (sg2 = 0; sg2 < 9u && hits2 < 16u; sg2++) {", "for (sg2 = 0; sg2 < 5u && hits2 < 16u; sg2++) {")
s = s.replace("uint32_t lim2 = (sg2 == 8u) ? 0x8000u : 0x20000u;", "uint32_t lim2 = 0x20000u;")
# widen keywords
s = s.replace("if (q3[0] == 'a' && q3[1] == 's' && q3[2] == 's' && q3[3] == 'e') { ok3 = 1; }",
              "if (q3[0] == 'a' && q3[1] == 's' && q3[2] == 's') { ok3 = 1; }\n\t\t\t\t\t\tif ((q3[0] == 'f' || q3[0] == 'F') && q3[1] == 'a' && q3[2] == 'i' && q3[3] == 'l') { ok3 = 1; }\n\t\t\t\t\t\tif (q3[0] == 'e' && q3[1] == 'r' && q3[2] == 'r') { ok3 = 1; }\n\t\t\t\t\t\tif (q3[0] == 'r' && q3[1] == 'i' && q3[2] == 'n' && q3[3] == 'g') { ok3 = 1; }\n\t\t\t\t\t\tif ((q3[0] == 'c' || q3[0] == 'C') && q3[1] == 'h' && q3[2] == 'a' && q3[3] == 'n') { ok3 = 1; }")
s = s.replace("if (k2 >= 8u) {", "if (k2 >= 10u) {")
io.open(p, "w", encoding="utf-8").write(s)
print("patched")