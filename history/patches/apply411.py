#!/usr/bin/env python3
"""apply-411: assert BT_EN (pin 65) and SW_CTRL (pin 153) together with WLAN_EN.

The real driver's log says "BTON: WLAN ON Asserting BT_EN to high" right when it brings the
radio up, and the venus device tree lists three enable pins for the cnss node:

    wlan-en-gpio   = <&tlmm 0x40 0>   pin 64   (we drive this one)
    qcom,bt-en-gpio = <&tlmm 0x41 0>  pin 65   (we never touch this one)
    qcom,sw-ctrl-gpio = <&tlmm 0x99 0> pin 153 (neither)

Only the MHI engine answers us today; every channel that lives in AMSS software (DIAG 4/5,
IPCR 20/21) is mute, while the two LOOPBACK channels work.  A half-powered core would look
exactly like that, so drive the other two enable pins high as well, before PERST# like the
vendor does.
"""
import io

SRC = "/root/hakios/xnu-src/xnu-8796.121.2/bsd/dev/hakios.pcie.c"

OLD = '''	wr(pin + TLMM_CFG, TLMM_CFG_OE);         /* function 0, the output enabled */
	wr(pin + TLMM_IO, TLMM_IO_OUT);          /* bit 1: drive it high */
	sleep_ms(10);
	printf("pcie: 4:   WLAN_EN (pin %u) driven high: CFG 0x%08x, IO 0x%08x\\n",
	       WLAN_EN_PIN, rd(pin + TLMM_CFG), rd(pin + TLMM_IO));
'''

NEW = '''	wr(pin + TLMM_CFG, TLMM_CFG_OE);         /* function 0, the output enabled */
	wr(pin + TLMM_IO, TLMM_IO_OUT);          /* bit 1: drive it high */
	/* apply-411: the other two enables the cnss node asks for, as the vendor drives them */
	{
		vm_offset_t bt = tlmm.base + 65u * TLMM_PIN_STRIDE;
		vm_offset_t sw = tlmm.base + 153u * TLMM_PIN_STRIDE;

		wr(bt + TLMM_CFG, TLMM_CFG_OE);
		wr(bt + TLMM_IO, TLMM_IO_OUT);
		wr(sw + TLMM_CFG, TLMM_CFG_OE);
		wr(sw + TLMM_IO, TLMM_IO_OUT);
		sleep_ms(2);
		printf("apply-411 bt_en (65) cfg 0x%08x io 0x%08x | sw_ctrl (153) cfg 0x%08x io 0x%08x\\n",
		    rd(bt + TLMM_CFG), rd(bt + TLMM_IO), rd(sw + TLMM_CFG), rd(sw + TLMM_IO));
	}
	sleep_ms(10);
	printf("pcie: 4:   WLAN_EN (pin %u) driven high: CFG 0x%08x, IO 0x%08x\\n",
	       WLAN_EN_PIN, rd(pin + TLMM_CFG), rd(pin + TLMM_IO));
'''

src = io.open(SRC, "r", encoding="utf-8", errors="surrogateescape").read()
assert src.count(OLD) == 1, "wlan_en body"
assert "apply-411" not in src
src = src.replace(OLD, NEW)
io.open(SRC, "w", encoding="utf-8", errors="surrogateescape").write(src)
print("apply-411 ok")
