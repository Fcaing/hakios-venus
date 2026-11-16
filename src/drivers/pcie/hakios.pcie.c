#include <sys/sysctl.h>
#include <stdarg.h>
#include <string.h>
/*
 * The PCIe root complex of the Xiaomi Mi 11 (SM8350, venus), and the road to the Wi-Fi chip
 * behind it -- a QCA6490 (WCN6855), vendor 0x17cb device 0x1103, which Android finds on
 * 0000:01:00.0 of this very controller.
 *
 * Nobody has run this controller from this kernel before, so it is walked in steps, and every
 * access is said before it is made: the loader watches this log from another core and writes it
 * to storage every two seconds, so a run that ends in a silent reset still leaves a note.
 *
 * The first attempt to read the branch clocks of the controller while its power domain (GDSC)
 * was still collapsed hung the machine: a register in a domain that is off does not answer.
 * So power comes first, and reads of the controller's own registers come after it:
 *
 *   1  reads   only what is powered whatever the state of the port -- the GLOBAL clock
 *              controller's always-on registers: the power domain's own switch (GDSC), the two
 *              branch-clock vote registers, and the port's reference clock enable
 *   2  writes  the power domain on and the branch clocks voted; releases the controller's and the
 *              PHY's resets; then reads the branch clocks, the PARF registers and the PHY status
 *   3  writes  the vendor's own PHY sequence (75 writes, from the device tree) and waits for the
 *              PCS status bit to say the PLL is up
 *   4  writes  PERST#, the reset line to the card, high; reads what the link then does
 *   5  reads   configuration space of bus 0 and bus 1 through the 1 MB ECAM window -- a vendor
 *              and device id of 17cb:1103 here is the whole point of this driver's first phase
 *
 * Boot-args: pcie=1 (default: run to pcie_step, which defaults to 1), pcie_step=N, pcie_only=K
 * (step K alone), pcie_pause=MS (default 300), pcie_fine=1 (pause before every access),
 * pcie_watch=S (say a word every second for S seconds at the end), pcie_return=1.
 *
 * Every number below is from the phone's own device tree and from Linux: drivers/pci/controller/
 * dwc/pcie-qcom.c, pcie-designware.c, drivers/phy/qualcomm/phy-qcom-qmp-pcie.c, drivers/clk/qcom/
 * gcc-sm8350.c, drivers/clk/qcom/gdsc.c, and the vendor DT's qcom,phy-sequence.
 */
#include <kern/clock.h>
#include <libkern/libkern.h>
#include <mach/mach_types.h>
#include <mach/vm_param.h>
#include <pexpert/pexpert.h>
#include <sys/hakios.input.h>
#include <sys/systm.h>
#include <vm/vm_kern.h>

extern vm_offset_t ml_io_map(vm_offset_t phys_addr, vm_size_t size);
extern void loader_log_putc(char c);

static uint32_t pcie_step_last = 1;
/*
 * The reading, kept for userland: the loader writes the kernel's log to the logdump
 * partition only in the first 24 seconds of a run, and the log ring keeps its newest
 * bytes, so a probe that runs late loses most of its own output.  Keep the numbers in a
 * string instead and let a tool read it: sysctl kern.hakios.pcie (see the end of this file).
 */
static char pcie_report[768];
static void pcie_note(const char *fmt, ...);

static uint32_t pcie_only, pcie_pause_ms = 300, pcie_fine, pcie_watch_seconds = 20, pcie_return;
static uint32_t pcie_step;
static uint32_t pcie_go = 1;	/* pcie_go=N: how far step 2 goes (1..6) */
static uint32_t pcie_no1;	/* pcie_no1=1: skip the ladder of step 1 */
extern int hakios_ufs_write_report(const char *name, const void *src, uint64_t len);
static uint32_t pcie_delay;
/*
 * The report as it stands, to the report partition if one was named (ufs_report_part=dbg): one
 * block, NUL padded. The host reads it back with dd of that partition's block device, which
 * takes milliseconds; the kernel log does not last long enough to be the channel.
 */
static void
pcie_flush(const char *stage)
{
	uint8_t block[4096];   /* a whole block of the report partition */
	size_t n = strlen(pcie_report);
	int error;

	if (n >= 4000) {
		n = 4000;
	}
	memset(block, 0, sizeof(block));
	memcpy(block, "PCIERPT1 ", 9);
	block[9] = (uint8_t)('0' + (pcie_step % 10));
	block[10] = ' ';
	memcpy(block + 11, stage, strlen(stage) < 16 ? strlen(stage) : 16);
	memcpy(block + 40, pcie_report, n);
	error = hakios_ufs_write_report("dbg", block, sizeof(block));
	printf("pcie: report to dbg at stage %s: %s, error %d (%u bytes of report)\n", stage,
	    error == 0 ? "written" : (error == ENOENT ? "no such partition" : (error == EROFS ? "not the report partition" : "failed")),
	    error, (uint32_t)n);
}
  /* pcie_delay=N: wait this many seconds before the first register */
static uint32_t pcie_after;	/* pcie_after=1: with pcie_power, read the controller too */
static uint32_t pcie_norails;	/* pcie_norails=1: do not vote the root's or the radio's rails */
static uint32_t pcie_power;	/* pcie_power=1: level 5 only: un-collapse the power domain */
static uint32_t pcie_power_only;	/* pcie_power_only=1: stop after the domain comes up */
static uint32_t pcie_vote;
static uint32_t pcie_reset;	/* pcie_reset=1: assert and release the resets at level 4 */	/* pcie_vote=1: release the collapse vote as well */	/* pcie_go=N: how far step 2 goes (1..6) */

static int say(const char *format, ...) __printflike(1, 2);

static int
say(const char *format, ...)
{
	char line[400];
	va_list list;

	va_start(list, format);
	vsnprintf(line, sizeof(line), format, list);
	va_end(list);
	for (const char *c = line; *c != 0; c++) {
		loader_log_putc(*c);
	}
	return printf("%s", line);
}
#define printf say

static void
sleep_us(uint32_t us)
{
	delay_for_interval(us, NSEC_PER_USEC);
}

static void
sleep_ms(uint32_t ms)
{
	delay_for_interval(ms, NSEC_PER_MSEC);
}

/* One plain load or store, as the GPU driver explains: the compiler does not get to choose. */
static uint32_t __attribute__((noinline))
rd(vm_offset_t address)
{
	uint32_t value;

	if (pcie_fine) {
		sleep_ms(pcie_pause_ms);
	}
	__asm__ volatile ("ldr %w0, [%1]" : "=r" (value) : "r" (address) : "memory");
	return value;
}

static void __attribute__((noinline))
wr(vm_offset_t address, uint32_t value)
{
	if (pcie_fine) {
		sleep_ms(pcie_pause_ms);
	}
	__asm__ volatile ("str %w0, [%1]" : : "r" (value), "r" (address) : "memory");
}

struct block {
	const char *name;
	uint32_t phys, size;
	vm_offset_t base;
};

static struct block parf  = { "parf",  0x1c00000, 0x3000, 0 };
static struct block phy   = { "phy",   0x1c06000, 0x2000, 0 };
static struct block dbi   = { "dbi",   0x60000000, 0x1000, 0 };
static struct block conf  = { "conf",  0x60100000, 0x100000, 0 };
static struct block gcc   = { "gcc",   0x100000, 0x1f0000, 0 };  /* the whole clock controller:
                                                                    its branch clocks reach 0x6b028 */
static struct block tlmm  = { "tlmm",  0xf100000, 0x100000, 0 };
/* the RPMh resource state coordinator, the DRV window the device tree calls drv-id 2 */
static struct block rsc   = { "rsc",   0x18220000, 0x10000, 0 };

static uint32_t cmddb_address(const char *name);
static bool rsc_supply_on(const char *name, unsigned millivolts);
static struct block elbi  = { "elbi",  0x60000f20, 0xa8, 0 };   /* as the touch driver: GPIO_CFG(n) = tlmm + 0x1000 * n */

static bool
need(struct block *b)
{
	if (b->base == 0) {
		b->base = ml_io_map(b->phys, b->size);
		if (b->base == 0) {
			printf("pcie: %u: cannot map %s at 0x%x\n", pcie_step, b->name, b->phys);
			return false;
		}
		printf("pcie: %u: %s at 0x%x, 0x%x bytes\n", pcie_step, b->name, b->phys, b->size);
	}
	return true;
}

/* ---- the phone's numbers ------------------------------------------------------------------------- */

/*
 * The global clock controller (gcc-sm8350.c). Its branch clocks are not enabled by their own
 * CBCR bit 0 (that is U-Boot's way); each of them has an enable bit in one of the two vote
 * registers below, and the CBCR only reports status in bit 31 (off) / bit 1 (hardware gated).
 */
#define GCC_CBCR_SLV_AXI               0x6b014
#define GCC_CBCR_MSTR_AXI              0x6b01c
#define GCC_CBCR_CFG_AHB               0x6b024
#define GCC_CBCR_AUX                   0x6b028
#define GCC_CBCR_PHY_RCHNG             0x6b038
#define GCC_CBCR_SLV_Q2A               0x6b010
#define GCC_CBCR_AGGRE0                0x6b080
#define GCC_CBCR_AGGRE1                0x8d084
#define GCC_CBCR_DDRSS_SF_TBU          0x8d080
#define GCC_CBCR_TBU                   0x9000c
#define GCC_CLKREF_EN                  0x8c004
#define GCC_GDSCR                      0x6b004
#define GCC_PCIE_BCR                   0x6b000
#define GCC_PCIE_PHY_BCR               0x6c01c

#define GCC_VOTE_0                     0x52000 /* bits 11 aggre1, 12 aggre0, 18 tbu, 19 ddrss, 22 phy_rchng */
#define GCC_VOTE_1                     0x52008 /* bits 0 slv_axi, 1 mstr_axi, 2 cfg_ahb, 3 aux, 5 slv_q2a */

#define VOTE_0_MASK                    0x004c0c00u
#define VOTE_1_MASK			0x0000003fu /* bits 0..5: the pipe clock is bit 4 */

#define CBCR_OFF                       0x80000000u /* bit 31: the branch says it is off */
#define CBCR_HWCG                      0x2         /* bit 1: hardware-gated, the halt check does not apply */

#define GCC_COLLAPSE_VOTE              0x152128    /* qcom,collapse-vote: 0 releases */
#define GDSC_SW_COLLAPSE               0x1         /* bit 0: 1 = collapsed, 0 = on */
#define GDSC_PWR_ON                    0x80000000u /* bit 31: says the domain is on */

/* The controller's own block (pcie-qcom.c). */
#define PARF_SYS_CTRL                  0x00
#define PARF_PHY_CTRL                  0x40
#define PARF_PHY_REFCLK                0x4c
#define PARF_CONFIG_BITS               0x50
#define PARF_DBI_BASE_ADDR             0x168
#define PARF_SLV_ADDR_SPACE_SIZE       0x16c
#define PARF_LTSSM                     0x1b0
#define PARF_DEVICE_TYPE               0x1000

#define PHY_SW_RESET                   0x200
#define PHY_STATUS                     0x214   /* 0x214 = pcs (0x200) + 0x14, qcom,phy-status-offset */
#define PHY_STATUS_BIT                 6       /* qcom,phy-status-bit; READY WHEN CLEAR (Linux polls !) */
#define PHY_POWER_DOWN                 0x240   /* qcom,phy-power-down-offset */
#define PHY_START_CTRL                 0x244

#define PERST_PIN                      94      /* qcom,perst-gpio */
#define TLMM_PIN_STRIDE                0x1000
#define TLMM_CFG                       0x0
#define TLMM_IO                        0x4
#define TLMM_IO_OE                     0x2     /* bit 1: drive the pin */
#define TLMM_IO_OUT                    0x2     /* bit 1: the level driven, as the touch driver writes it */
#define TLMM_CFG_OE                    0x200   /* bit 9: the pin drives */

/*
 * The vendor's PHY bring-up, 75 register writes, in venus.pcie.h -- generated from the device
 * tree's own qcom,phy-sequence by venus-recon/pcie-phy-seq.py, not written by hand.
 */
#include "venus.pcie.h"

/* the loader writes the log to flash every 2 s for the first 24 s: a pause after each
 * message makes the last one on flash the one that names the register that hangs */
static uint32_t pcie_settle_ms = 2200;   /* pcie_settle=300: how long to wait between steps */
#define PCIE_SETTLE_MS pcie_settle_ms
/* the same idea, for the reads that come after the port is powered: they fit in the window */
#define PCIE_AFTER_SETTLE_MS 60

/* ---- step 1: the always-on part of the clock controller ---------------------------------------- */

static void
read_what_is_always_on(void)
{
	uint32_t v;

	/*
	 * One register per message, and a pause between the message and the read: for the first
	 * NOTE_SECONDS (24 s) of the kernel's life the loader writes this log to the logdump
	 * partition every two seconds, so the message naming the register about to be read is on
	 * flash before the read that may hang the machine -- which makes the last line of the
	 * partition the answer to "which register".
	 */
	printf("pcie: 1: GCC is mapped; each register is named before it is read\n");
	sleep_ms(PCIE_SETTLE_MS);

#define PCIE_READ(n, name, reg) \
	printf("pcie: 1: read %d: " name "\n", n); \
	sleep_ms(PCIE_SETTLE_MS); \
	v = rd(reg); \
	printf("pcie: 1:   " name " = 0x%08x\n", v)

	PCIE_READ(1, "the vote register 0x52000", gcc.base + GCC_VOTE_0);
	PCIE_READ(2, "the vote register 0x52008", gcc.base + GCC_VOTE_1);
	PCIE_READ(3, "the power domain's switch, GDSCR 0x6b004", gcc.base + GCC_GDSCR);
	PCIE_READ(4, "the reference clock, 0x8c004", gcc.base + GCC_CLKREF_EN);
	PCIE_READ(5, "the branch status of the auxiliary clock, 0x6b028", gcc.base + 0x6b028);

#undef PCIE_READ

	printf("pcie: 1: every register of the always-on part has been read\n");
}

/* ---- step 2: the power domain, the clocks, the resets ------------------------------------------ */

static bool
power_on(void)
{
	uint32_t v0, v1, gdscr, i;

	printf("pcie: 2: the port's power, level %u of 6 (pcie_go)\n", pcie_go);

	if (pcie_power) {
		printf("pcie: 2: power only (pcie_power=1): the domain, and nothing inside it\n");
		sleep_ms(PCIE_SETTLE_MS);
		/*
		 * The vendor's power_root() stage 2: the root complex has two rails of its
		 * own (PM8350 LDO6 1.2 V and LDO5 0.88 V), and they are voted through the
		 * RPMh DB before anything inside the controller is touched.  The star port
		 * does exactly this and it is what the phone's Android does too.
		 */
		if (!pcie_norails) {
			sleep_ms(PCIE_AFTER_SETTLE_MS);
			printf("pcie: 2:   the root's rails: ldob6 1200 mV, then ldob5 880 mV (RPMh)\n");
			bool a = rsc_supply_on("ldob6", 1200);
			bool b = a && rsc_supply_on("ldob5", 880);
			printf("pcie: 2:   rails %s (ldob6 %s, ldob5 %s)\n", (a && b) ? "voted" : "FAILED",
			       a ? "ok" : "no", b ? "ok" : "no");
			pcie_note("rails ldob6=%d ldob5=%d; ", a, b);
			if (!(a && b)) {
				printf("pcie: 2:   the rails are not there: nothing inside the port can be powered\n");
				return false;
			}
		}
		sleep_ms(PCIE_AFTER_SETTLE_MS);
		gdscr = rd(gcc.base + GCC_GDSCR);
		printf("pcie: 2:   GDSCR 0x6b004 = 0x%08x -> clear bit 0 (SW_COLLAPSE)\n", gdscr);		gdscr = rd(gcc.base + GCC_GDSCR);
		printf("pcie: 2:   GDSCR 0x6b004 = 0x%08x -> clear bit 0 (SW_COLLAPSE)\n", gdscr);
		sleep_ms(PCIE_SETTLE_MS);
		wr(gcc.base + GCC_GDSCR, gdscr & ~GDSC_SW_COLLAPSE);
		for (i = 0; i < 40; i++) {
			sleep_us(100);
			gdscr = rd(gcc.base + GCC_GDSCR);
			if (gdscr & GDSC_PWR_ON) {
				printf("pcie: 2:   the domain came up after %u polls of 100 us\n", i + 1);
			pcie_note("pcie: 2: gdscr 0x%08x after %u polls; ", gdscr, i + 1);
				break;
			}
		}
		/* the PARF side, as pci-msm.c does before the PHY (msm_pcie_enable) */
		printf("pcie: 2: parf device type 0x%08x -> 4 (RC)\n", rd(parf.base + 0x1000));
		wr(parf.base + 0x1000, 4);
		printf("pcie: 2: parf phy control 0x%08x -> clear bit 0\n", rd(parf.base + 0x0040));
		wr(parf.base + 0x0040, rd(parf.base + 0x0040) & ~1u);
		wr(parf.base + 0x0350, 0);		/* dbi base address */
		wr(parf.base + 0x0000, 0x365e);	/* sys control */
		printf("pcie: 2: parf sys control = 0x0000365e\n");
		wr(parf.base + 0x0174, rd(parf.base + 0x0174) & ~(1u << 4));
		wr(parf.base + 0x022c, 0);		/* interrupt mask */
		wr(parf.base + 0x0358, 0x4000000);	/* slv address space */
		wr(parf.base + 0x01a8, (1u << 31) | rd(parf.base + 0x01a8));
		printf("pcie: 2: parf ready: dbi 0, slv 0x4000000, axi halted\n");

		if (pcie_power_only) {
			printf("pcie: 2:   power only asked for: stopping before the votes (pcie_power_only=1)\n");
			pcie_flush("power");
			return true;
		}
		sleep_ms(PCIE_AFTER_SETTLE_MS);
		printf("pcie: 2:   the clock votes, now that the domain is on: 0x52008 |= 0x%08x, 0x52000 |= 0x%08x\n",
		       VOTE_1_MASK, VOTE_0_MASK);
		wr(gcc.base + GCC_VOTE_1, rd(gcc.base + GCC_VOTE_1) | VOTE_1_MASK);
		wr(gcc.base + GCC_VOTE_0, rd(gcc.base + GCC_VOTE_0) | VOTE_0_MASK);
		sleep_ms(2);
		printf("pcie: 2:   votes 0x52000 = 0x%08x, 0x52008 = 0x%08x\n", rd(gcc.base + GCC_VOTE_0),
		       rd(gcc.base + GCC_VOTE_1));
		pcie_note("votes 0x%08x/0x%08x; ", rd(gcc.base + GCC_VOTE_0), rd(gcc.base + GCC_VOTE_1));
		sleep_ms(PCIE_AFTER_SETTLE_MS);
		printf("pcie: 2:   the reference clock, 0x8c004 bit 0\n");
		wr(gcc.base + GCC_CLKREF_EN, rd(gcc.base + GCC_CLKREF_EN) | 1u);
		sleep_ms(2);
		printf("pcie: 2:   clkref 0x8c004 = 0x%08x, the branch status of the auxiliary clock 0x6b028 = 0x%08x\n",
		       rd(gcc.base + GCC_CLKREF_EN), rd(gcc.base + 0x6b028));

		/* the roots: bit 0 of the CFG register set means the root is off */
		{
			uint32_t a = rd(gcc.base + 0x6b058 + 4);
			uint32_t r = rd(gcc.base + 0x6b03c + 4);
			wr(gcc.base + 0x6b058 + 4, a & ~1u);
			wr(gcc.base + 0x6b03c + 4, r & ~1u);
			wr(gcc.base + 0x6b054, 0);
			printf("pcie: 2:   rcg aux 0x%08x -> 0x%08x, rchng 0x%08x -> 0x%08x, pipe mux 0x6b054 = 0 (the phy)\n",
			       a, a & ~1u, r, r & ~1u);
		}
		pcie_note("clkref 0x%08x aux 0x%08x; ", rd(gcc.base + GCC_CLKREF_EN), rd(gcc.base + 0x6b028));
		if (pcie_after) {
			sleep_ms(PCIE_AFTER_SETTLE_MS);
			printf("pcie: 2:   with the domain on, the controller\n");
			printf("pcie: 2:   SYS_CTRL 0x00 = 0x%08x, PHY_CTRL 0x40 = 0x%08x, REFCLK 0x4c = 0x%08x\n",
			       rd(parf.base + PARF_SYS_CTRL), rd(parf.base + PARF_PHY_CTRL),
			       rd(parf.base + PARF_PHY_REFCLK));
			pcie_note("parf SYS_CTRL 0x%08x PHY_CTRL 0x%08x REFCLK 0x%08x; ",
			          rd(parf.base + PARF_SYS_CTRL), rd(parf.base + PARF_PHY_CTRL),
			          rd(parf.base + PARF_PHY_REFCLK));
			sleep_ms(PCIE_AFTER_SETTLE_MS);
			printf("pcie: 2:   CONFIG_BITS 0x50 = 0x%08x, DEVICE_TYPE 0x1000 = 0x%08x\n",
			       rd(parf.base + PARF_CONFIG_BITS), rd(parf.base + PARF_DEVICE_TYPE));
			sleep_ms(PCIE_AFTER_SETTLE_MS);
			printf("pcie: 2:   LTSSM 0x1b0 = 0x%08x, DBI_BASE 0x168 = 0x%08x, SLV_SIZE 0x16c = 0x%08x\n",
			       rd(parf.base + PARF_LTSSM), rd(parf.base + PARF_DBI_BASE_ADDR),
			       rd(parf.base + PARF_SLV_ADDR_SPACE_SIZE));
			sleep_ms(PCIE_AFTER_SETTLE_MS);
			printf("pcie: 2:   the PHY: SW_RESET 0x200 = 0x%08x, STATUS 0x214 = 0x%08x, POWER_DOWN 0x240 = 0x%08x\n",
			       rd(phy.base + PHY_SW_RESET), rd(phy.base + PHY_STATUS),
			       rd(phy.base + PHY_POWER_DOWN));
			sleep_ms(PCIE_AFTER_SETTLE_MS);
			printf("pcie: 2:   the DesignWare core: ID 0x000 = 0x%08x, CMD 0x004 = 0x%08x, PORT_DEBUG1 0x72c = 0x%08x\n",
			       rd(dbi.base + 0x0), rd(dbi.base + 0x4), rd(dbi.base + 0x72c));
			sleep_ms(PCIE_AFTER_SETTLE_MS);
			printf("pcie: 2:   the port, in one line: LTSSM 0x%08x, PHY STATUS 0x%08x, PHY POWER_DOWN 0x%08x, "
			       "DBI ID 0x%08x, PORT_DEBUG1 0x%08x, device 0x%08x\n",
			       rd(parf.base + PARF_LTSSM), rd(phy.base + PHY_STATUS), rd(phy.base + PHY_POWER_DOWN),
			       rd(dbi.base + 0x0), rd(dbi.base + 0x72c),
			       rd(conf.base + ((0u << 15) | (1u << 12) | (0u << 8) | 0u)));
		}
		printf("pcie: 2:   GDSCR 0x6b004 = 0x%08x (%s)\n", gdscr,
		       (gdscr & GDSC_PWR_ON) ? "the domain is on" : "the domain is OFF");
		if (!(gdscr & GDSC_PWR_ON)) {
			return false;
		}
		/* the port is powered and its clocks are voted: the steps after this one run on it */
		printf("pcie: 2:   the port is powered; the PHY, PERST# and the bus follow\n");
		return true;
	}


#define REPORT_STATE() do { \
		gdscr = rd(gcc.base + GCC_GDSCR); \
		v0 = rd(gcc.base + GCC_VOTE_0); \
		v1 = rd(gcc.base + GCC_VOTE_1); \
		printf("pcie: 2:   GDSCR 0x6b004 = 0x%08x (%s), votes 0x%08x / 0x%08x, clkref 0x8c004 = 0x%08x\n", \
		       gdscr, (gdscr & GDSC_PWR_ON) ? "the domain is on" : "the domain is OFF", \
		       v0, v1, rd(gcc.base + GCC_CLKREF_EN)); \
		printf("pcie: 2:   slv_axi 0x%08x mstr_axi 0x%08x cfg_ahb 0x%08x aux 0x%08x\n", \
		       rd(gcc.base + GCC_CBCR_SLV_AXI), rd(gcc.base + GCC_CBCR_MSTR_AXI), \
		       rd(gcc.base + GCC_CBCR_CFG_AHB), rd(gcc.base + GCC_CBCR_AUX)); \
		printf("pcie: 2:   slv_q2a 0x%08x phy_rchng 0x%08x aggre0 0x%08x aggre1 0x%08x\n", \
		       rd(gcc.base + GCC_CBCR_SLV_Q2A), rd(gcc.base + GCC_CBCR_PHY_RCHNG), \
		       rd(gcc.base + GCC_CBCR_AGGRE0), rd(gcc.base + GCC_CBCR_AGGRE1)); \
		printf("pcie: 2:   tbu 0x%08x ddrss_sf_tbu 0x%08x\n", \
		       rd(gcc.base + GCC_CBCR_TBU), rd(gcc.base + GCC_CBCR_DDRSS_SF_TBU)); \
	} while (0)

	/* level 1: nothing is written; this is the state the phone is handed over in */
	printf("pcie: 2: level 1: reading the clock controller, writing nothing\n");
	sleep_ms(PCIE_SETTLE_MS);
	REPORT_STATE();
	if (pcie_go < 2) {
		return (rd(gcc.base + GCC_GDSCR) & GDSC_PWR_ON) != 0;
	}

	/* level 2: the nine branch clocks, by the bits of the two vote registers */
	printf("pcie: 2: level 2: voting for the branch clocks: 0x52008 |= 0x%08x, 0x52000 |= 0x%08x\n",
	       VOTE_1_MASK, VOTE_0_MASK);
	sleep_ms(PCIE_SETTLE_MS);
	wr(gcc.base + GCC_VOTE_1, rd(gcc.base + GCC_VOTE_1) | VOTE_1_MASK);
	wr(gcc.base + GCC_VOTE_0, rd(gcc.base + GCC_VOTE_0) | VOTE_0_MASK);
	sleep_ms(2);
	REPORT_STATE();
	if (pcie_go < 3) {
		return (rd(gcc.base + GCC_GDSCR) & GDSC_PWR_ON) != 0;
	}

	/* level 3: the reference clock the PHY and the core both want */
	printf("pcie: 2: level 3: the reference clock's enable bit, 0x8c004 bit 0\n");
	sleep_ms(PCIE_SETTLE_MS);
	wr(gcc.base + GCC_CLKREF_EN, rd(gcc.base + GCC_CLKREF_EN) | 1u);
	sleep_ms(2);
	REPORT_STATE();
	if (pcie_go < 4) {
		return (rd(gcc.base + GCC_GDSCR) & GDSC_PWR_ON) != 0;
	}

	/* level 4: the two resets of the clock controller, asserted then released */
	printf("pcie: 2: level 4: the resets, GCC_PCIE_0_BCR 0x6b000 and GCC_PCIE_0_PHY_BCR 0x6c01c%s\n",
	       pcie_reset ? " (asserting and releasing them)" : " (only read: pcie_reset=1 writes them)");
	sleep_ms(PCIE_SETTLE_MS);
	printf("pcie: 2:   before: core 0x%08x, phy 0x%08x, the collapse vote 0x%08x\n",
	       rd(gcc.base + GCC_PCIE_BCR), rd(gcc.base + GCC_PCIE_PHY_BCR),
	       rd(gcc.base + GCC_COLLAPSE_VOTE));
	if (pcie_reset) {
		wr(gcc.base + GCC_PCIE_BCR, rd(gcc.base + GCC_PCIE_BCR) | 1u);
		sleep_ms(2);
		wr(gcc.base + GCC_PCIE_BCR, rd(gcc.base + GCC_PCIE_BCR) & ~1u);
		sleep_ms(2);
		wr(gcc.base + GCC_PCIE_PHY_BCR, rd(gcc.base + GCC_PCIE_PHY_BCR) | 1u);
		sleep_us(250);
		wr(gcc.base + GCC_PCIE_PHY_BCR, rd(gcc.base + GCC_PCIE_PHY_BCR) & ~1u);
		sleep_ms(2);
		printf("pcie: 2:   after:  core 0x%08x, phy 0x%08x\n", rd(gcc.base + GCC_PCIE_BCR),
		       rd(gcc.base + GCC_PCIE_PHY_BCR));
	}
	REPORT_STATE();
	if (pcie_vote) {
		printf("pcie: 2: level 4: the collapse vote, 0x152128 = 0x%08x -> 0\n",
		       rd(gcc.base + GCC_COLLAPSE_VOTE));
		sleep_ms(PCIE_SETTLE_MS);
		wr(gcc.base + GCC_COLLAPSE_VOTE, 0);
		sleep_ms(2);
		printf("pcie: 2:   the collapse vote now 0x%08x\n", rd(gcc.base + GCC_COLLAPSE_VOTE));
		REPORT_STATE();
	}
	if (pcie_go < 5) {
		return (rd(gcc.base + GCC_GDSCR) & GDSC_PWR_ON) != 0;
	}

	/* level 5: the power domain itself */
	printf("pcie: 2: level 5: the power domain on: the collapse vote 0x%08x, GDSCR 0x%08x\n",
	       rd(gcc.base + GCC_COLLAPSE_VOTE), rd(gcc.base + GCC_GDSCR));
	sleep_ms(PCIE_SETTLE_MS);
	printf("pcie: 2:   releasing the collapse vote: 0x152128 = 0\n");
	wr(gcc.base + GCC_COLLAPSE_VOTE, 0);
	sleep_ms(2);
	gdscr = rd(gcc.base + GCC_GDSCR);
	wr(gcc.base + GCC_GDSCR, gdscr & ~GDSC_SW_COLLAPSE);
	for (i = 0; i < 20; i++) {
		sleep_us(100);
		if (rd(gcc.base + GCC_GDSCR) & GDSC_PWR_ON) {
			printf("pcie: 2:   the domain came up after %u polls of 100 µs\n", i + 1);
			break;
		}
	}
	REPORT_STATE();
	if (pcie_go < 6) {
		return (rd(gcc.base + GCC_GDSCR) & GDSC_PWR_ON) != 0;
	}

	/* level 6: the controller's own registers */
	printf("pcie: 2: level 6: the controller's own registers, now that it is powered\n");
	sleep_ms(PCIE_SETTLE_MS);
	printf("pcie: 2:   SYS_CTRL 0x00 = 0x%08x, PHY_CTRL 0x40 = 0x%08x, REFCLK 0x4c = 0x%08x\n",
	       rd(parf.base + PARF_SYS_CTRL), rd(parf.base + PARF_PHY_CTRL), rd(parf.base + PARF_PHY_REFCLK));
	printf("pcie: 2:   CONFIG_BITS 0x50 = 0x%08x, DEVICE_TYPE 0x1000 = 0x%08x\n",
	       rd(parf.base + PARF_CONFIG_BITS), rd(parf.base + PARF_DEVICE_TYPE));
	printf("pcie: 2:   LTSSM 0x1b0 = 0x%08x, DBI_BASE 0x168 = 0x%08x, SLV_SIZE 0x16c = 0x%08x\n",
	       rd(parf.base + PARF_LTSSM), rd(parf.base + PARF_DBI_BASE_ADDR),
	       rd(parf.base + PARF_SLV_ADDR_SPACE_SIZE));
	printf("pcie: 2:   the PHY: SW_RESET 0x200 = 0x%08x, STATUS 0x214 = 0x%08x, POWER_DOWN 0x240 = 0x%08x\n",
	       rd(phy.base + PHY_SW_RESET), rd(phy.base + PHY_STATUS), rd(phy.base + PHY_POWER_DOWN));
	printf("pcie: 2:   the DesignWare core: ID 0x000 = 0x%08x, CMD 0x004 = 0x%08x, PORT_DEBUG1 0x72c = 0x%08x\n",
	       rd(dbi.base + 0x0), rd(dbi.base + 0x4), rd(dbi.base + 0x72c));

#undef REPORT_STATE

	return (rd(gcc.base + GCC_GDSCR) & GDSC_PWR_ON) != 0;
}

/* ---- step 3: the vendor's PHY sequence ---------------------------------------------------------- */

static bool
phy_start(void)
{
	uint32_t i, v;

	printf("pcie: 3: %u writes of the vendor's PHY sequence at 0x%x\n", VENUS_PCIE_PHY_SEQ_LEN,
	       phy.phys);
	for (i = 0; i < VENUS_PCIE_PHY_SEQ_LEN; i++) {
		wr(phy.base + venus_pcie_phy_seq[i].offset, venus_pcie_phy_seq[i].value);
		if (venus_pcie_phy_seq[i].delay_us) {
			sleep_us(venus_pcie_phy_seq[i].delay_us);
		}
	}
	v = rd(phy.base + PHY_STATUS);
	printf("pcie: 3:   after the sequence: STATUS 0x%08x (bit %u %s), SW_RESET 0x%08x, START 0x%08x\n",
	       v, PHY_STATUS_BIT, (v & (1u << PHY_STATUS_BIT)) ? "set" : "clear",
	       rd(phy.base + PHY_SW_RESET), rd(phy.base + PHY_START_CTRL));
	sleep_ms(1);
	/* Linux waits for the PCS status bit to become CLEAR (phy-qcom-qmp-pcie.c:4870). */
	for (i = 0; i < 50; i++) {
		v = rd(phy.base + PHY_STATUS);
		if ((v & (1u << PHY_STATUS_BIT)) == 0) {
			printf("pcie: 3:   the PCS status bit cleared at %u x 200 us: 0x%08x\n", i, v);
			return true;
		}
		sleep_us(200);
	}
	printf("pcie: 3:   the PCS status bit stays set: 0x%08x\n", v);
	return false;
}

/* ---- step 4: PERST#, then what the link does ---------------------------------------------------- */

/*
 * The chip is powered through the pin the device tree calls wlan-en-gpio: <&tlmm 0x40 0>, so pin 64,
 * driven high by cnss2 on Android. Without it the radio is not on the bus, and the receiver detection
 * of the link training never sees a partner (LTSSM stays in DETECT_QUIET, state 0).
 */
#define WLAN_EN_PIN 64

static void
wlan_en(void)
{
	vm_offset_t pin = tlmm.base + WLAN_EN_PIN * TLMM_PIN_STRIDE;

	wr(pin + TLMM_CFG, TLMM_CFG_OE);         /* function 0, the output enabled */
	wr(pin + TLMM_IO, TLMM_IO_OUT);          /* bit 1: drive it high */
	sleep_ms(10);
	printf("pcie: 4:   WLAN_EN (pin %u) driven high: CFG 0x%08x, IO 0x%08x\n",
	       WLAN_EN_PIN, rd(pin + TLMM_CFG), rd(pin + TLMM_IO));
}

static void
perst(bool high)
{
	vm_offset_t pin = tlmm.base + PERST_PIN * TLMM_PIN_STRIDE;

	wr(pin + TLMM_CFG, TLMM_CFG_OE);            /* function 0, the output enabled (bit 9) */
	wr(pin + TLMM_IO, high ? TLMM_IO_OUT : 0);
	printf("pcie: 4:   PERST# (pin %u) %s: IO 0x%08x\n", PERST_PIN, high ? "high" : "low",
	       rd(pin + TLMM_IO));
}

/*
 * The vendor's own DBI configuration before the link is asked to train:
 * pci-msm.c msm_pcie_link_train(). All offsets are from PCIe's root complex DBI.
 */
static void
link_train_config(void)
{
	uint32_t v;

	if (!need(&dbi)) {
		printf("pcie: 4:   no DBI to configure the link with\n");
		return;
	}

	/* GEN3_GEN2_CTRL 0x080c: field 0x1f00 = 1 */
	v = rd(dbi.base + 0x080c);
	wr(dbi.base + 0x080c, (v & ~0x1f00u) | (1u << 8));

	/* GEN3_EQ_CONTROL 0x08a8: bit 5 */
	wr(dbi.base + 0x08a8, rd(dbi.base + 0x08a8) | 0x20u);

	/* GEN3_RELATED 0x0890: bit 0 = 0 */
	wr(dbi.base + 0x0890, rd(dbi.base + 0x0890) & ~1u);

	/* GEN3_MISC_CONTROL 0x08bc bit 0 = 1, SPCIE_CAP 0x0154 = the preset, then bit 0 = 0 */
	wr(dbi.base + 0x08bc, rd(dbi.base + 0x08bc) | 1u);
	wr(dbi.base + 0x0154, 0);
	wr(dbi.base + 0x08bc, rd(dbi.base + 0x08bc) & ~1u);

	/* DEVICE_CONTROL_STATUS 0x0078: max TLP read size, 128 bytes */
	v = rd(dbi.base + 0x0078);
	wr(dbi.base + 0x0078, (v & ~0x7000u) | (5u << 12));

	printf("pcie: 4:   the DBI is configured: GEN3_GEN2_CTRL 0x080c = 0x%08x, "
	       "EQ_CONTROL 0x08a8 = 0x%08x, SPCIE_CAP 0x0154 = 0x%08x\n",
	       rd(dbi.base + 0x080c), rd(dbi.base + 0x08a8), rd(dbi.base + 0x0154));
}

static void
link_train_start(void)
{
	uint32_t v = rd(parf.base + PARF_LTSSM);

	printf("pcie: 4:   LTSSM 0x1b0 = 0x%08x -> set bit 8 (the vendor's write_mask(0, BIT(8)) sets it)\n", v);
	wr(parf.base + PARF_LTSSM, v | (1u << 8));
	wr(parf.base + PARF_LTSSM, v | (1u << 8));
}

static void
link_state(const char *when)
{
	uint32_t ltssm = rd(parf.base + PARF_LTSSM);
	uint32_t stts;

	need(&elbi);
	stts = elbi.base ? rd(elbi.base + 0x08) : 0;   /* PCIE20_ELBI_SYS_STTS: bit 10 link up, 12..17 the state */

	printf("pcie: 4: %s: LTSSM 0x%08x (state %u), PHY 0x%08x, DBI 0x72c 0x%08x, ELBI 0x08 0x%08x (link %s, state %u)\n",
	       when, ltssm, ltssm & 0x3f, rd(phy.base + PHY_STATUS), rd(dbi.base + 0x72c), stts,
	       (stts & (1u << 10)) ? "up" : "down", (stts >> 12) & 0x3f);
	pcie_note("LTSSM 0x%08x ELBI 0x%08x %s state %u; ", ltssm, stts,
	          (stts & (1u << 10)) ? "up" : "down", (stts >> 12) & 0x3f);
}

/* ---- step 5: configuration space through the ECAM window ---------------------------------------- */

static uint32_t
config_read(uint32_t bus, uint32_t device, uint32_t function, uint32_t reg)
{
	return rd(conf.base + (bus << 15) + (device << 12) + (function << 8) + reg);
}

static void
config_space(void)
{
	uint32_t bus, device;

	for (bus = 0; bus < 2; bus++) {
		for (device = 0; device < 1; device++) {
			uint32_t id = config_read(bus, device, 0, 0x0);
			uint32_t class = config_read(bus, device, 0, 0x8);

			printf("pcie: 5: %02u:%02u.0 id 0x%08x (vendor 0x%04x device 0x%04x) class 0x%06x rev 0x%02x\n",
			       bus, device, id, id & 0xffff, id >> 16, class >> 8, class & 0xff);
			printf("pcie: 5:   cmd/status 0x%08x, header 0x%08x, BAR0 0x%08x\n",
			       config_read(bus, device, 0, 0x4), config_read(bus, device, 0, 0xc),
			       config_read(bus, device, 0, 0x10));
		}
	}
}


/* ---- the command DB ---------------------------------------------------------------------------- */

/*
 * The command DB (drivers/soc/qcom/cmd-db.c): a read only table, prepared by the bootloader, that
 * maps a resource name to the address the RPMh wants a vote written to.  Its header is small and
 * the entries are 24 bytes each:
 *
 *   cmd_db_header: version(4) magic(4) = db 30 03 0c, rsc_hdr[8] (16 bytes each), checksum,
 *                  reserved, then the data the rsc_hdr offsets are relative to
 *   entry_header:  id[8], priority[2], addr, len, offset
 *
 * The five rails the radio needs are looked up by these names, so this prints every entry.
 */
struct cmd_db_rsc {
	uint16_t slv_id;
	uint16_t header_offset;
	uint16_t data_offset;
	uint16_t cnt;
	uint16_t version;
	uint16_t reserved[3];
} __attribute__((packed));

struct cmd_db_entry {
	uint8_t id[8];
	uint32_t priority[2];
	uint32_t addr;
	uint16_t len;
	uint16_t offset;
} __attribute__((packed));

static struct block cmd_db = { "cmd-db", 0x80860000, 0x20000, 0 };

static void
cmddb_dump(void)
{
	uint8_t *base;
	struct cmd_db_rsc *rsc;
	uint8_t *data;
	uint32_t version;
	int i, j;

	if (!need(&cmd_db)) {
		return;
	}
	base = (uint8_t *)cmd_db.base;

	version = rd((vm_offset_t)base);
	printf("cmddb: magic %02x %02x %02x %02x, version %u\n",
	       base[4], base[5], base[6], base[7], version);
	if (base[4] != 0xdb || base[5] != 0x30 || base[6] != 0x03 || base[7] != 0x0c) {
		printf("cmddb: not the command DB (first words %08x %08x)\n",
		       version, rd((vm_offset_t)base + 4));
		return;
	}

	rsc = (struct cmd_db_rsc *)(base + 8);
	data = base + 144;              /* version, magic, 8 rsc headers, checksum, reserved */
	for (i = 0; i < 8; i++) {
		uint8_t *at;
		int n;

		if (rsc[i].slv_id == 0) {
			break;
		}
		n = rsc[i].cnt;
		printf("cmddb: slave %u: %d entries, header +%u, data +%u\n",
		       rsc[i].slv_id, n, rsc[i].header_offset, rsc[i].data_offset);
		at = data + rsc[i].header_offset;
		for (j = 0; j < n; j++, at += sizeof(struct cmd_db_entry)) {
			struct cmd_db_entry *e = (struct cmd_db_entry *)at;
			printf("cmddb:  %c%c%c%c%c%c%c%c 0x%08x\n",
			       e->id[0], e->id[1], e->id[2], e->id[3],
			       e->id[4], e->id[5], e->id[6], e->id[7], e->addr);
		}
	}
}

/* ---- the RPMh supplies, as the star port does them ---------------------------------------------- */

/*
 * A command DB id is eight bytes, NUL padded: "ldob5", "smpb10", "smpe2"...  The address in the
 * entry is the RPMh resource address the RSC wants in its command word.
 */
static uint32_t
cmddb_address(const char *name)
{
	struct cmd_db_rsc *rscs;
	uint8_t *base;
	char id[8] = { 0 };
	uint32_t i, j;

	if (strlen(name) > 8 || !need(&cmd_db)) {
		return 0;
	}
	memcpy(id, name, strlen(name));
	base = (uint8_t *)cmd_db.base;
	if (memcmp(base + 4, "\xdb\x30\x03\x0c", 4) != 0) {
		return 0;
	}
	rscs = (struct cmd_db_rsc *)(base + 8);
	for (i = 0; i < 8; i++) {
		uint32_t n = rscs[i].cnt;

		if (rscs[i].slv_id == 0 || n > 512) {
			continue;
		}
		struct cmd_db_entry *e = (struct cmd_db_entry *)(base + 144 + rscs[i].header_offset);
		for (j = 0; j < n; j++) {
			if (memcmp(e[j].id, id, 8) == 0) {
				return e[j].addr;
			}
		}
	}
	return 0;
}

/*
 * One RPMh "active only" vote through the RSC's TCS: the slot is taken, the three command words
 * are written (the resource address +0/+8/+4, the values millivolts/7/1), the trigger is rung,
 * and completion and the return to idle are both waited for.  This is the star port's
 * supply_on_locked() against the device tree's qcom,tcs-offset 0xd00 and drv-id 2.
 */
static bool
rsc_supply_on(const char *name, unsigned millivolts)
{
	uint32_t address = cmddb_address(name);
	vm_offset_t t;
	uint32_t old_irq, old_control, old_wait, old_enable, old_commands[3][3];
	static const uint32_t offsets[3] = { 0, 8, 4 };
	uint32_t values[3];
	uint32_t i, j;
	bool done = false, idle = false;

	if (address == 0 || ((address >> 16) & 15u) != 4u) {
		printf("pcie: rsc: %s: no RPMh address in the command DB (0x%08x)\n", name, address);
		return false;
	}
	values[0] = millivolts;
	values[1] = 7;
	values[2] = 1;
	if (!need(&rsc)) {
		return false;
	}
	t = rsc.base + 0xd00;
	for (i = 0; i < 1000; i++) {
		if (rd(t + 0x18) != 0) {
			break;
		}
		sleep_us(100);
	}
	if (i == 1000) {
		printf("pcie: rsc: %s: the slot never went idle\n", name);
		return false;
	}
	if (rd(t + 4) & 1u) {
		printf("pcie: rsc: %s: a completion is pending; not voting\n", name);
		return false;
	}
	old_irq = rd(t);
	old_control = rd(t + 0x14);
	old_wait = rd(t + 0x10);
	old_enable = rd(t + 0x1c);
	for (i = 0; i < 3; i++) {
		for (j = 0; j < 3; j++) {
			old_commands[i][j] = rd(t + 0x30 + 20 * i + 4 * j);
		}
	}
	wr(t + 0x14, old_control & ~(1u << 24));
	wr(t + 0x14, old_control & ~((1u << 24) | (1u << 16)));
	wr(t + 8, 1);
	for (i = 0; i < 3; i++) {
		wr(t + 0x30 + 20 * i, 0x10108);      /* four bytes, write, response */
		wr(t + 0x34 + 20 * i, address + offsets[i]);
		wr(t + 0x38 + 20 * i, values[i]);
	}
	wr(t + 0x10, 7);
	wr(t + 0x1c, 7);
	wr(t, old_irq | 1u);
	wr(t + 0x14, 1u << 16);
	wr(t + 0x14, (1u << 16) | (1u << 24));
	for (i = 0; i < 2000; i++) {
		if (rd(t + 4) & 1u) {
			done = true;
			break;
		}
		sleep_us(100);
	}
	if (done) {
		for (i = 0; i < 1000; i++) {
			if (rd(t + 0x18) != 0) {
				idle = true;
				break;
			}
			sleep_us(100);
		}
	}
	wr(t + 0x14, rd(t + 0x14) & ~(1u << 24));
	wr(t + 0x14, rd(t + 0x14) & ~(1u << 16));
	wr(t + 0x1c, 0);
	wr(t + 8, 1);
	for (i = 0; i < 3; i++) {
		for (j = 0; j < 3; j++) {
			wr(t + 0x30 + 20 * i + 4 * j, old_commands[i][j]);
		}
	}
	wr(t + 0x10, old_wait);
	wr(t + 0x1c, old_enable);
	wr(t, old_irq);
	wr(t + 0x14, old_control & ~(1u << 24));
	printf("pcie: rsc: %s %u mV: done %d idle %d (address 0x%08x)\n", name, millivolts, done, idle, address);
	return done && idle;
}

/* the radio's six rails, in the vendor's order and voltages (venus' device tree) */
static bool
radio_rails(void)
{
	static const struct { const char *name; unsigned millivolts; } rails[] = {
		{ "smpb10", 1800 },      /* vdd-wlan-io */
		{ "ldoe7",  2700 },      /* vdd-wlan-sp2t */
		{ "smpe2",   950 },      /* vdd-wlan-aon */
		{ "smpb11",  950 },      /* vdd-wlan-dig */
		{ "smpc1",  1900 },      /* vdd-wlan-rfa1 */
		{ "smpb12", 1350 },      /* vdd-wlan-rfa2 */
	};
	uint32_t i;

	for (i = 0; i < sizeof(rails) / sizeof(rails[0]); i++) {
		uint32_t at = cmddb_address(rails[i].name);

		printf("pcie: 4:   %s at 0x%08x for %u mV\n", rails[i].name, at, rails[i].millivolts);
		if (at == 0) {
			/* the command DB does not carry this one: the antenna switch is often left out */
			printf("pcie: 4:   %s is not in the command DB: skipped\n", rails[i].name);
			continue;
		}
		if (!rsc_supply_on(rails[i].name, rails[i].millivolts)) {
			printf("pcie: 4:   %s did not take the vote\n", rails[i].name);
			return false;
		}
	}
	printf("pcie: 4:   the radio's rails are voted\n");
	pcie_note("radio rails voted; ");
	sleep_ms(100);   /* WLAN_ENABLE_DELAY, the vendor's 1 s is for the full sequence */
	return true;
}

/* Gen1, no ASPM: the low half of the link control registers only (status bits are W1C) */
static void
gen1_config(void)
{
	uint32_t control = rd(dbi.base + 0xa0);
	uint32_t link = rd(dbi.base + 0x80);

	wr(dbi.base + 0xa0, (control & ~0xfu) | 1u);
	wr(dbi.base + 0x80, link & ~3u);
	printf("pcie: 4:   Gen1: 0xa0 0x%08x -> 0x%08x, 0x80 0x%08x -> 0x%08x\n",
	       control, (control & ~0xfu) | 1u, link, link & ~3u);
}

/* ---- the run ------------------------------------------------------------------------------------*//* ---- the run ----------------------------------------------------------------------------------- */

void
hakios_pcie_init(void)
{
	if (PE_parse_boot_argn("pcie_delay", &pcie_delay, sizeof(pcie_delay)) && pcie_delay != 0) {
		printf("pcie: waiting %u s before the first register (pcie_delay): writing the power domain's switch early hangs the machine\n", pcie_delay);
		sleep_ms(pcie_delay * 1000);
	}
	uint32_t asked = 0;

	{
		uint32_t cmddb = 0;

		if (PE_parse_boot_argn("cmddb", &cmddb, sizeof(cmddb)) && cmddb != 0) {
			cmddb_dump();
			if (cmddb == 2) {
				return;         /* cmddb=2: only the dump */
			}
		}
	}
	if (!PE_parse_boot_argn("pcie", &asked, sizeof(asked)) || asked == 0) {
		return;                         /* nothing here is touched unless asked for */
	}
	if (!PE_parse_boot_argn("pcie_step", &pcie_step_last, sizeof(pcie_step_last))) {
		pcie_step_last = 1;
	}
	PE_parse_boot_argn("pcie_only", &pcie_only, sizeof(pcie_only));
	PE_parse_boot_argn("pcie_go", &pcie_go, sizeof(pcie_go));
	PE_parse_boot_argn("pcie_vote", &pcie_vote, sizeof(pcie_vote));
	PE_parse_boot_argn("pcie_power", &pcie_power, sizeof(pcie_power));
	PE_parse_boot_argn("pcie_power_only", &pcie_power_only, sizeof(pcie_power_only));
	PE_parse_boot_argn("pcie_norails", &pcie_norails, sizeof(pcie_norails));
	PE_parse_boot_argn("pcie_after", &pcie_after, sizeof(pcie_after));
	PE_parse_boot_argn("pcie_no1", &pcie_no1, sizeof(pcie_no1));
	PE_parse_boot_argn("pcie_reset", &pcie_reset, sizeof(pcie_reset));
	PE_parse_boot_argn("pcie_pause", &pcie_pause_ms, sizeof(pcie_pause_ms));
	PE_parse_boot_argn("pcie_settle", &pcie_settle_ms, sizeof(pcie_settle_ms));
	PE_parse_boot_argn("pcie_fine", &pcie_fine, sizeof(pcie_fine));
	PE_parse_boot_argn("pcie_watch", &pcie_watch_seconds, sizeof(pcie_watch_seconds));
	PE_parse_boot_argn("pcie_return", &pcie_return, sizeof(pcie_return));

	pcie_flush("start");
	printf("pcie: the root complex of this phone, up to step %u%s\n", pcie_step_last,
	       pcie_only ? " (one step)" : "");

	for (pcie_step = 1; pcie_step <= pcie_step_last; pcie_step++) {
		if (pcie_only != 0 && pcie_step != pcie_only) {
			continue;
		}
		if (!need(&gcc)) {
			return;
		}
		if (pcie_step >= 2 && (!need(&parf) || !need(&phy) || !need(&dbi))) {
			return;
		}
		if (pcie_step >= 4 && !need(&tlmm)) {
			return;
		}
		if (pcie_step >= 5 && !need(&conf)) {
			return;
		}
		sleep_ms(pcie_pause_ms);
		switch (pcie_step) {
		case 1:
			if (!pcie_no1) {
		read_what_is_always_on();
		pcie_flush("step");
	}
			break;
		case 2:
			if (!power_on()) {
				printf("pcie: 2: the power domain did not come on: stopping here\n");
				return;
			}
			break;
		case 3:
			if (!phy_start()) {
				printf("pcie: 3: the PHY is not up: stopping here\n");
				return;
			}
			break;
		case 4:
			/*
			 * The order is the vendor's (power_root stages 9 and 10, as the star
			 * port implements them): the radio's six rails, WLAN_EN, then Gen1 with
			 * ASPM off, then PERST# up, then the training start, then the ELBI
			 * status -- not the DesignWare PORT_DEBUG1 register.
			 */
			if (!pcie_norails && !radio_rails()) {
				printf("pcie: 4:   the radio's rails are not there: stopping here\n");
				return;
			}
			wlan_en();
			perst(false);
			sleep_ms(20);
			gen1_config();
			sleep_ms(10);
			perst(true);
			sleep_ms(20);
			link_train_start();
			{
				bool linked = false;
				for (uint32_t i = 0; i < 100; i++) {
					uint32_t elbi_status = need(&elbi) ? rd(elbi.base + 0x08) : 0;
					uint32_t link_control = rd(dbi.base + 0x80);
					if ((elbi_status & (1u << 10)) && (link_control & (1u << 29))) {
						linked = true;
						break;
					}
					sleep_ms(5);
				}
				printf("pcie: 4:   link %s: ELBI 0x08 = 0x%08x, DBI 0x80 = 0x%08x, LTSSM 0x%08x\n",
				       linked ? "UP" : "down", need(&elbi) ? rd(elbi.base + 0x08) : 0,
				       rd(dbi.base + 0x80), rd(parf.base + PARF_LTSSM));
				pcie_note("link %d elbi 0x%08x dbi80 0x%08x ltssm 0x%08x; ", linked,
				          need(&elbi) ? rd(elbi.base + 0x08) : 0, rd(dbi.base + 0x80),
				          rd(parf.base + PARF_LTSSM));
			}
			link_state("after PERST# and the training start");
			pcie_flush("link");
			break;
		case 5:
			config_space();
			break;
		default:
			printf("pcie: %u: there is no such step\n", pcie_step);
			return;
		}
	}

	if (pcie_watch_seconds) {
		uint32_t i;

		/*
		 * The kernel's log ring keeps only its newest bytes, so a line that is
		 * printed once at the end of the probe is pushed out by everything the
		 * rest of the boot prints before the loader flushes.  Say the same
		 * summary every second instead: whichever flush lands, the tail of the
		 * partition is then a line with the values in it.
		 */
		for (i = 0; i < pcie_watch_seconds; i++) {
			uint32_t ltssm = need(&parf) ? rd(parf.base + PARF_LTSSM) : 0;
			uint32_t status = need(&phy) ? rd(phy.base + PHY_STATUS) : 0;
			uint32_t pwrdn = need(&phy) ? rd(phy.base + PHY_POWER_DOWN) : 0;
			uint32_t dbid = need(&dbi) ? rd(dbi.base + 0x0) : 0;
			uint32_t dbg1 = need(&dbi) ? rd(dbi.base + 0x72c) : 0;
			uint32_t sysc = need(&parf) ? rd(parf.base + PARF_SYS_CTRL) : 0;
			uint32_t devt = need(&parf) ? rd(parf.base + PARF_DEVICE_TYPE) : 0;
			uint32_t gdsc = need(&gcc) ? rd(gcc.base + GCC_GDSCR) : 0;

			pcie_note("pcie watch %u of %u: LTSSM 0x%08x PHY_STATUS 0x%08x PHY_POWER_DOWN 0x%08x "
			          "DBI_ID 0x%08x PORT_DEBUG1 0x%08x SYS_CTRL 0x%08x DEVICE_TYPE 0x%08x GDSCR 0x%08x",
			          i + 1, pcie_watch_seconds, ltssm, status, pwrdn, dbid, dbg1, sysc, devt, gdsc);
			printf("pcie: watch %u of %u s\n", i + 1, pcie_watch_seconds);
			sleep_ms(1000);
		}
	}
}

/* ---- the reading, for userland ---------------------------------------------------------------- */

static void
pcie_note(const char *fmt, ...)
{
	va_list ap;
	size_t n = strlen(pcie_report);

	if (n >= sizeof(pcie_report) - 2) {
		n = 0;
	}
	va_start(ap, fmt);
	vsnprintf(pcie_report + n, sizeof(pcie_report) - n, fmt, ap);
	va_end(ap);
}

SYSCTL_DECL(_kern_hakios);
SYSCTL_STRING(_kern_hakios, OID_AUTO, pcie, CTLFLAG_RD | CTLFLAG_LOCKED, pcie_report, 0,
              "the PCIe root complex's last reading (drivers/pcie/hakios.pcie.c)");
