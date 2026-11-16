/*
 * What is on the phone's power-management chips, and what time their clock says. Only with boot-arg pmic=1.
 *
 * The phone's PMICs (the PMK8350 and PM7325 beside the SoC, with a PM8350C and others on the board) hang on
 * one serial bus, SPMI, and the SoC reaches them through the "PMIC arbiter" (dt: qcom,spmi@c440000). Each chip
 * is a set of small blocks ("peripherals", 256 registers each) with a type and a subtype in registers 0x04
 * and 0x05: a GPIO, a regulator, the power-on block, a temperature alarm, a flash LED driver, a charger, the
 * real-time clock. Android's drivers find theirs from the device tree. This one asks the arbiter what it has
 * and what each block says it is, and puts the answer in the log: an inventory, so that the next driver to
 * be written for one of these blocks starts from what the phone really has instead of from what a table
 * for another phone says (this phone's device tree has no node for its real-time clock, for instance).
 *
 * THIS DRIVER ONLY READS. It reads through the arbiter's "observer" channels exactly as drivers/input/hakios.buttons.c
 * does, one bus transfer at a time under the same lock (hakios_spmi_lock()), and writes only the command word
 * that asks the arbiter for a read. Nothing is written to a PMIC: they make the phone's supplies. Where the arbiter
 * answers "denied" or "failed" for a block, the line says so and the driver goes on.
 *
 * Register layout and the version (5) of the arbiter: Linux drivers/spmi/spmi-pmic-arb.c, as drivers/input/hakios.buttons.c
 * has it and has run it on this phone. A phone whose arbiter is another version gets one line and nothing else.
 *
 * The clock. The PMICs have a real-time clock that Android sets, and keeps while the phone is off (Linux:
 * rtc-pm8xxx.c). When the inventory finds a block of type 0x07 (the clock) it reads four bytes at register 0x48 of
 * the one with subtype 0x01 -- the seconds since 1970, little-endian, as Linux reads them -- twice, a little over a
 * second apart, and says whether the second is later than the first (it ticks), how many days that is, and what the
 * kernel's own time (the loader gives the kernel the host's time in epoch=) minus it comes to. The value is kept as
 * kern.hakios.rtc_seconds. The kernel's own clock is NOT set from it. (The first run on the phone showed why: the
 * counter reads 60110539 seconds, 695 days of counting, which as a date is 1971. It is a counter, not wall-clock time; see
 * the comment at the report.)
 *
 * Status (what has and has not been seen): RUN ON THE PHONE (POCO X5 Pro, 2026-10-27, four runs): the arbiter is version 0x50020000
 * (5.2) with 512 channels, 444 distinct peripherals; slaves 0 to 3 answer (0, 1 and 2 are the PMK8350, PM7325 and PM8350C, as the buttons and flashlight drivers have them), the
 * peripherals of slaves 4, 8 and 9 answer "failed" (no chip there: 98 of them); the clock is found where Linux has it
 * (slave 0 0x6100, type 0x07 subtype 0x01) and ticks once a second. The access is the buttons driver's, which is
 * known to work on this phone; what is new is the walk over all channels and the clock's registers (0x48 for the read), taken from Linux's rtc-pm8xxx.c
 * as remembered. The first run on the phone (2026-10-27) found the clock's blocks where Linux has them: slave 0 0x6100 is type 0x07
 * subtype 0x01 (the write block) and 0x6200 type 0x07 subtype 0x03 (the alarm); the type is 0x07, not the 0x06 first assumed. Nothing here has a recorded run on the phone until a
 * line below says so; it is not run in QEMU, which has no arbiter.
 *
 * Boot-args:
 *   pmic=1            do it (once, from a thread of its own)
 *   pmic_list=0       only the clock, not the inventory of every block
 */
#include <kern/clock.h>
#include <kern/locks.h>
#include <kern/startup.h>
#include <kern/thread.h>
#include <kern/thread_call.h>
#include <libkern/libkern.h>
#include <mach/mach_types.h>
#include <pexpert/pexpert.h>
#include <sys/sysctl.h>
#include <sys/systm.h>

extern vm_offset_t ml_io_map(vm_offset_t phys_addr, vm_size_t size);
extern void loader_log_putc(char c);
extern void hakios_spmi_lock(void);
extern void hakios_spmi_unlock(void);

SYSCTL_DECL(_kern_hakios);

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

static inline uint32_t
rd(vm_offset_t address)
{
	return *(volatile uint32_t *)address;
}

static inline void
wr(vm_offset_t address, uint32_t value)
{
	*(volatile uint32_t *)address = value;
}

/* the arbiter, as drivers/input/hakios.buttons.c maps it */
#define ARB_CORE_PHYS           0x0c440000UL
#define ARB_CORE_SIZE           0x1100UL
#define ARB_CNFG_PHYS           0x0c40a000UL
#define ARB_CNFG_SIZE           0x1000UL
#define ARB_OBSERVER_PHYS       0x0e600000UL
#define ARB_OBSERVER_SIZE       0x10000UL
#define ARB_SYSTEM              0
#define ARB_VERSION             0x000
#define ARB_VERSION_5           0x50000000u
#define ARB_VERSION_7           0x70000000u
#define ARB_FEATURES            0x004
#define ARB_CHANNEL(n)          (0x900 + 4 * (n))               /* [19:8] slave and peripheral */
#define ARB_MAX_CHANNELS        512
#define OBSERVER_COMMAND        0x00
#define OBSERVER_STATUS         0x08
#define OBSERVER_DATA0          0x18
#define OBSERVER_DATA1          0x1c
#define STATUS_DONE             0x1
#define STATUS_FAILURE          0x2
#define STATUS_DENIED           0x4
#define STATUS_DROPPED          0x8
#define COMMAND_READ            (1u << 27)
#define READ_TIMEOUT_US         2000

static vm_offset_t arb_core, arb_observer;

/* Read `count` (1 to 8) registers of the peripheral at channel `channel`, from register `reg`; NULL, or what went wrong. */
static const char *
spmi_read(uint32_t channel, uint8_t reg, uint8_t *bytes, uint32_t count)
{
	vm_offset_t ch = arb_observer + 0x10000UL * ARB_SYSTEM + 0x80UL * channel;
	uint64_t start = mach_absolute_time(), now, interval;
	uint32_t status, data[2];

	nanoseconds_to_absolutetime(READ_TIMEOUT_US * (uint64_t)NSEC_PER_USEC, &interval);
	hakios_spmi_lock();
	wr(ch + OBSERVER_COMMAND, COMMAND_READ | (uint32_t)reg << 4 | (count - 1));
	do {
		status = rd(ch + OBSERVER_STATUS);
		now = mach_absolute_time();
	} while (!(status & STATUS_DONE) && now - start < interval);
	data[0] = rd(ch + OBSERVER_DATA0);
	data[1] = count > 4 ? rd(ch + OBSERVER_DATA1) : 0;
	hakios_spmi_unlock();

	if (!(status & STATUS_DONE)) {
		return "no answer";
	} else if (status & STATUS_DENIED) {
		return "denied";
	} else if (status & STATUS_FAILURE) {
		return "failed";
	} else if (status & STATUS_DROPPED) {
		return "dropped";
	}
	for (uint32_t i = 0; i < count; i++) {
		bytes[i] = (uint8_t)(data[i / 4] >> (8 * (i % 4)));
	}
	return NULL;
}

/* ---- the write path -------------------------------------------------------------------------------------- */

#define CORE_CMD                0x00
#define CORE_STATUS             0x08
#define CORE_WDATA0             0x10
#define CORE_WDATA1             0x14
#define COMMAND_WRITE           (0x40u << 27)
#define WRITE_TIMEOUT_US        2000
#define PAGE_STRIDE             0x10000UL

/* Write `count` (1 to 8) registers of the peripheral at channel `channel`, from register `reg`; NULL, or what went wrong. */
static const char *
spmi_write(uint32_t channel, uint8_t reg, const uint8_t *bytes, uint32_t count)
{
	vm_offset_t ch = arb_core + PAGE_STRIDE * channel;
	uint64_t start = mach_absolute_time(), now, interval;
	uint32_t status, word0 = 0, word1 = 0;

	if (channel >= ARB_MAX_CHANNELS || count == 0 || count > 8) {
		return "bad arguments";
	}
	for (uint32_t i = 0; i < count && i < 4; i++) {
		word0 |= (uint32_t)bytes[i] << (8 * i);
	}
	for (uint32_t i = 4; i < count; i++) {
		word1 |= (uint32_t)bytes[i] << (8 * (i - 4));
	}
	nanoseconds_to_absolutetime(WRITE_TIMEOUT_US * (uint64_t)NSEC_PER_USEC, &interval);
	hakios_spmi_lock();
	wr(ch + CORE_WDATA0, word0);
	if (count > 4) {
		wr(ch + CORE_WDATA1, word1);
	}
	wr(ch + CORE_CMD, COMMAND_WRITE | ((uint32_t)reg << 4) | (count - 1));
	do {
		status = rd(ch + CORE_STATUS);
		now = mach_absolute_time();
	} while (!(status & STATUS_DONE) && now - start < interval);
	hakios_spmi_unlock();

	if (!(status & STATUS_DONE)) {
		return "no answer";
	} else if (status & STATUS_DENIED) {
		return "denied (this execution environment does not own the channel)";
	} else if (status & STATUS_FAILURE) {
		return "failed";
	} else if (status & STATUS_DROPPED) {
		return "dropped";
	}
	return NULL;
}


/* ---- the inventory --------------------------------------------------------------------------------------- */

#define REG_TYPE                0x04
#define RTC_TYPE                0x07
#define RTC_SUBTYPE_WRITE       0x01
#define RTC_REG_READ            0x48

static int64_t rtc_seconds_value = -1;
static int pmic_peripherals_value;
SYSCTL_QUAD(_kern_hakios, OID_AUTO, rtc_seconds, CTLFLAG_RD | CTLFLAG_LOCKED, &rtc_seconds_value,
    "the PMIC real-time clock, seconds since 1970 as it read once at boot; -1: not read");
SYSCTL_INT(_kern_hakios, OID_AUTO, pmic_peripherals, CTLFLAG_RD | CTLFLAG_LOCKED, &pmic_peripherals_value, 0,
    "how many blocks of the power-management chips the arbiter showed us");

static uint8_t seen_type[ARB_MAX_CHANNELS][2];
static uint16_t ppids[ARB_MAX_CHANNELS];
static uint16_t channel_of[ARB_MAX_CHANNELS];

static bool
read_clock(uint32_t channel, uint32_t *seconds)
{
	uint8_t b[4];
	const char *problem = spmi_read(channel, RTC_REG_READ, b, 4);

	if (problem != NULL) {
		say("pmic: the clock's seconds: %s\n", problem);
		return false;
	}
	*seconds = b[0] | (uint32_t)b[1] << 8 | (uint32_t)b[2] << 16 | (uint32_t)b[3] << 24;
	return true;
}

static void
clock_report(uint32_t channel)
{
	uint32_t first, second;
	clock_sec_t kernel_seconds;
	clock_usec_t kernel_micro;

	if (!read_clock(channel, &first)) {
		return;
	}
	delay_for_interval(1100, NSEC_PER_MSEC);
	if (!read_clock(channel, &second)) {
		return;
	}
	clock_get_calendar_microtime(&kernel_seconds, &kernel_micro);
	rtc_seconds_value = second;
	/*
	 * What this counter is, as the first run on the phone showed: it ticks once a second, and it is NOT wall-clock time (it
	 * read 60110539, which as a date is in 1971). Qualcomm phones keep the clock as a free-running counter in the PMIC, and
	 * Android's time service keeps the offset to real time in a file of its own; the counter's use to this kernel is a
	 * count of seconds that goes on through a reboot and a flat battery's worth of power-off. If the kernel was given the
	 * host's time (epoch=), the difference printed is that offset, which can be compared with the file's.
	 */
	say("pmic: the real-time clock reads %u, then %u a second and a tenth later (%s); that is %u days of counting, not a date;"
	    " the kernel's time minus it is %lld s\n", first, second, second > first ? "it ticks" : "IT DOES NOT TICK", second / 86400,
	    (long long)kernel_seconds - (long long)second);
}

static bool list_all = true;

static void
pmic_run(__unused thread_call_param_t p0, __unused thread_call_param_t p1)
{
	bool list = list_all;
	uint32_t version, channels, found = 0, rtc_channel = 0;
	bool rtc_found = false;

	arb_core = ml_io_map(ARB_CORE_PHYS, ARB_CORE_SIZE);
	arb_observer = ml_io_map(ARB_OBSERVER_PHYS, ARB_OBSERVER_SIZE);
	if (arb_core == 0 || arb_observer == 0) {
		say("pmic: could not map the PMIC arbiter\n");
		goto out;
	}
	version = rd(arb_core + ARB_VERSION);
	channels = rd(arb_core + ARB_FEATURES) & 0x7ff;
	say("pmic: PMIC arbiter version %#x, %u channels\n", version, channels);
	if (version < ARB_VERSION_5 || version >= ARB_VERSION_7) {
		say("pmic: this driver knows version 5 of the arbiter only: nothing read\n");
		goto out;
	}
	if (channels == 0 || channels > ARB_MAX_CHANNELS) {
		channels = ARB_MAX_CHANNELS;
	}
	/* one entry for each distinct slave/peripheral, with the first channel that reaches it */
	for (uint32_t n = 0; n < channels; n++) {
		uint32_t map = rd(arb_core + ARB_CHANNEL(n));
		uint16_t ppid = (uint16_t)((map >> 8) & 0xfff);
		bool again = false;

		if (map == 0) {
			continue;
		}
		for (uint32_t i = 0; i < found; i++) {
			if (ppids[i] == ppid) {
				again = true;
				break;
			}
		}
		if (!again) {
			ppids[found] = ppid;
			channel_of[found] = (uint16_t)n;
			found++;
		}
	}
	pmic_peripherals_value = (int)found;
	say("pmic: %u distinct peripherals in the arbiter's table; reading the type of each\n", found);
	for (uint32_t i = 0; i < found; i++) {
		uint8_t is[2] = { 0xff, 0xff };
		const char *problem = spmi_read(channel_of[i], REG_TYPE, is, 2);

		seen_type[i][0] = is[0];
		seen_type[i][1] = is[1];
		if (list) {
			if (problem != NULL) {
				say("pmic:   slave %u 0x%02x00 (channel %u): %s\n", ppids[i] >> 8, ppids[i] & 0xff, channel_of[i], problem);
			} else {
				say("pmic:   slave %u 0x%02x00 (channel %u): type %#04x subtype %#04x\n", ppids[i] >> 8, ppids[i] & 0xff,
				    channel_of[i], is[0], is[1]);
			}
		}
		if (problem == NULL && is[0] == RTC_TYPE && is[1] == RTC_SUBTYPE_WRITE && !rtc_found) {
			rtc_found = true;
			rtc_channel = channel_of[i];
			say("pmic: the real-time clock is slave %u 0x%02x00 (type %#x, subtype %#x)\n", ppids[i] >> 8, ppids[i] & 0xff,
			    is[0], is[1]);
		}
	}
	if (rtc_found) {
		clock_report(rtc_channel);
	} else {
		say("pmic: none of the %u blocks says it is a real-time clock (type %#x, subtype %#x): none read\n", found, RTC_TYPE,
		    RTC_SUBTYPE_WRITE);
	}
out:
	return;
}

/* pmic_poke=1: write pmic_value to pmic_reg of the peripheral at (pmic_slave, pmic_usid), read it back. */
static void
pmic_poke(uint32_t slave, uint32_t usid, uint32_t reg, uint32_t value)
{
	uint8_t out[4], in[4];
	uint16_t wanted = (uint16_t)((slave << 8) | usid);
	const char *problem = "no such peripheral";
	uint32_t channel = 0, i;

	for (i = 0; i < (uint32_t)pmic_peripherals_value; i++) {
		if (ppids[i] == wanted) {
			channel = channel_of[i];
			problem = NULL;
			break;
		}
	}
	if (problem != NULL) {
		say("pmic: poke: %s (slave %u 0x%02x00)\n", problem, slave, usid);
		return;
	}
	out[0] = (uint8_t)(value & 0xff);
	out[1] = (uint8_t)((value >> 8) & 0xff);
	out[2] = (uint8_t)((value >> 16) & 0xff);
	out[3] = (uint8_t)((value >> 24) & 0xff);
	say("pmic: poke: slave %u 0x%02x00 (channel %u) register 0x%02x <- 0x%08x\n", slave, usid, channel, reg, value);
	problem = spmi_read(channel, (uint8_t)reg, in, 4);
	if (problem != NULL) {
		say("pmic: poke: the register could not be read first: %s\n", problem);
		return;
	}
	say("pmic: poke:   before 0x%02x%02x%02x%02x\n", in[3], in[2], in[1], in[0]);
	problem = spmi_write(channel, (uint8_t)reg, out, 4);
	if (problem != NULL) {
		say("pmic: poke: the write did not happen: %s\n", problem);
		return;
	}
	problem = spmi_read(channel, (uint8_t)reg, in, 4);
	if (problem != NULL) {
		say("pmic: poke:   the write went through, but the read back failed: %s\n", problem);
		return;
	}
	say("pmic: poke:   after  0x%02x%02x%02x%02x\n", in[3], in[2], in[1], in[0]);
}

/* pmic_dump=1: read pmic_count bytes from pmic_reg of pmic_usid...pmic_usid+pmic_usid_count-1 on
 * pmic_slave, 4 at a time, and print them.  Reads only: this is how we find an LDO's voltage and
 * enable registers before writing them. */
static void
pmic_dump(uint32_t slave, uint32_t usid, uint32_t reg, uint32_t count)
{
	uint8_t in[4];
	uint32_t channel, i, u, run = 1;

	if (count == 0 || count > 64) {
		count = 16;
	}
	(void)PE_parse_boot_argn("pmic_usid_count", &run, sizeof(run));
	if (run == 0 || run > 32) {
		run = 1;
	}
	for (u = 0; u < run; u++) {
		uint16_t wanted = (uint16_t)((slave << 8) | (usid + u));
		const char *problem = "no such peripheral";

		channel = 0;
		for (i = 0; i < (uint32_t)pmic_peripherals_value; i++) {
			if (ppids[i] == wanted) {
				channel = channel_of[i];
				problem = NULL;
				break;
			}
		}
		if (problem != NULL) {
			say("pmic: dump: slave %u 0x%02x00: %s\n", slave, usid + u, problem);
			continue;
		}
		say("pmic: dump: slave %u 0x%02x00 (channel %u), registers 0x%02x..0x%02x\n", slave, usid + u,
		    channel, reg, reg + count - 1);
		for (i = 0; i <= count - 4; i += 4) {
			problem = spmi_read(channel, (uint8_t)(reg + i), in, 4);
			if (problem != NULL) {
				say("pmic: dump:   0x%02x: %s\n", reg + i, problem);
				continue;
			}
			say("pmic: dump:   0x%02x = 0x%02x 0x%02x 0x%02x 0x%02x\n", reg + i, in[0], in[1], in[2], in[3]);
		}
	}
}

__startup_func
static void
pmic_init(void)
{
	uint32_t enabled = 0, list = 1;

	if (!PE_parse_boot_argn("pmic", &enabled, sizeof(enabled)) || !enabled) {
		return;
	}
	(void)PE_parse_boot_argn("pmic_list", &list, sizeof(list));
	list_all = list != 0;
	{
		uint32_t now = 0, inline_done = 0;

		/* pmic_now=1: do it here and now, so the loader still owns the storage and writes the log */
		if (PE_parse_boot_argn("pmic_now", &now, sizeof(now)) && now) {
			say("pmic: the inventory and the pokes run on the startup thread\n");
			pmic_run(NULL, NULL);
			inline_done = 1;
		}
		if (!inline_done) {
			/* once, from a thread call: the reads wait on the bus, and that is no place for the startup thread */
			thread_call_enter(thread_call_allocate(pmic_run, NULL));
		}
	}

	{
		uint32_t poke = 0, slave = 0, usid = 0, reg = 0, value = 0;

		if (PE_parse_boot_argn("pmic_dump", &poke, sizeof(poke)) && poke) {
			(void)PE_parse_boot_argn("pmic_slave", &slave, sizeof(slave));
			(void)PE_parse_boot_argn("pmic_usid", &usid, sizeof(usid));
			(void)PE_parse_boot_argn("pmic_reg", &reg, sizeof(reg));
			if (!PE_parse_boot_argn("pmic_count", &value, sizeof(value))) {
				value = 16;
			}
			pmic_dump(slave, usid, reg, value);
		}
		if (PE_parse_boot_argn("pmic_poke", &poke, sizeof(poke)) && poke) {
			(void)PE_parse_boot_argn("pmic_slave", &slave, sizeof(slave));
			(void)PE_parse_boot_argn("pmic_usid", &usid, sizeof(usid));
			(void)PE_parse_boot_argn("pmic_reg", &reg, sizeof(reg));
			(void)PE_parse_boot_argn("pmic_value", &value, sizeof(value));
			pmic_poke(slave, usid, reg, value);
		}
		/* the same thing three more times, so one boot can switch two rails and check them */
		{
			static const char *const more[3] = { "2", "3", "4" };
			uint32_t n;

			for (n = 0; n < 3; n++) {
				char name[32];
				uint32_t again = 0;

				snprintf(name, sizeof(name), "pmic_poke%s", more[n]);
				if (!PE_parse_boot_argn(name, &again, sizeof(again)) || !again) {
					continue;
				}
				snprintf(name, sizeof(name), "pmic_slave%s", more[n]);
				(void)PE_parse_boot_argn(name, &slave, sizeof(slave));
				snprintf(name, sizeof(name), "pmic_usid%s", more[n]);
				(void)PE_parse_boot_argn(name, &usid, sizeof(usid));
				snprintf(name, sizeof(name), "pmic_reg%s", more[n]);
				(void)PE_parse_boot_argn(name, &reg, sizeof(reg));
				snprintf(name, sizeof(name), "pmic_value%s", more[n]);
				(void)PE_parse_boot_argn(name, &value, sizeof(value));
				pmic_poke(slave, usid, reg, value);
			}
		}
	}
}
STARTUP(EARLY_BOOT, STARTUP_RANK_LAST, pmic_init);
