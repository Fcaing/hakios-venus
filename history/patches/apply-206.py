import io, sys
p = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"
s = io.open(p, encoding="utf-8").read()
def sub(old, new):
    global s
    assert s.count(old) == 1, (old, s.count(old))
    s = s.replace(old, new)
sub('{ "ldoe7",  2700 },      /* vdd-wlan-sp2t */',
    '{ "ldoe7",  2800 },      /* vdd-wlan-sp2t, venus ant-switch-config 0x2ab980 */')
sub('{ "smpe2",   950 },      /* vdd-wlan-aon */',
    '{ "smpe2",  1012 },      /* vdd-wlan-aon, venus aon-config 0xf7120 */')
sub('{ "smpb11",  950 },      /* vdd-wlan-dig */',
    '{ "smpb11", 1012 },      /* vdd-wlan-dig, venus dig-config 0xf7120 */')
io.open(p, "w", encoding="utf-8").write(s)
print("ok rails")