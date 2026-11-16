import io
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
lines = io.open(p, encoding="utf-8").read().split("\n")
for i, l in enumerate(lines):
    if l.strip() == "wr(bar0.base + 0x300 + 20 * 8, (uint32_t)trewp);" and "rd(" not in l:
        indent = l[:len(l) - len(l.lstrip())]
        ins = [
            indent + "/* the vendor wakes the device before every channel doorbell:",
            indent + "   mhi_toggle_dev_wake() writes 1 then 0 to the wake doorbell at",
            indent + "   CHDBOFF + 8 * MHI_DEV_WAKE_DB (127).  Maybe it sits in M2. */",
            indent + "wr(bar0.base + 0x300 + 8u * 127u, 1u);",
            indent + "wr(bar0.base + 0x300 + 8u * 127u, 0u);",
            indent + 'printf("apply-298 woke the device: wake db 0x%08x now %u, mh 0x%08x\\n",',
            indent + "       (uint32_t)(0x300 + 8u * 127u), (unsigned)rd(bar0.base + 0x300 + 8u * 127u), rd(bar0.base + 0x48));",
        ]
        lines[i:i] = ins
        break
else:
    raise SystemExit("anchor not found")
io.open(p, "w", encoding="utf-8").write("\n".join(lines))
print("patched")