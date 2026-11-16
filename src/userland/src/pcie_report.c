/*
 * pcie_report: read sysctl kern.hakios.pcie and print it (drivers/pcie/hakios.pcie.c keeps it).
 *
 * The kernel's own log is unreliable for a late-printing driver: the loader writes the log to
 * the logdump partition only in the first 24 seconds of a run, and the ring holds its newest
 * bytes.  The driver keeps its numbers in this string instead; userland is a place where
 * printing works.
 *
 * A copy goes to the data volume whether or not the sysctl answers, so that the host can tell
 * "the job never ran" from "the sysctl was empty" without a screenshot.
 */

#include <errno.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <sys/sysctl.h>

static void
write_file(const char *path, const char *text)
{
	FILE *f = fopen(path, "w");

	if (f != NULL) {
		fprintf(f, "%s\n", text);
		fclose(f);
	}
}

int
main(void)
{
	char buf[1024];
	char line[1200];
	size_t len = sizeof(buf);
	int n;

	write_file("/private/var/pcie-ran.txt", "pcie_report ran");
	write_file("/private/var/mobile/tmp/pcie-ran.txt", "pcie_report ran");
	write_file("/private/var/root/pcie-ran.txt", "pcie_report ran");

	memset(buf, 0, sizeof(buf));
	n = sysctlbyname("kern.hakios.pcie", buf, &len, NULL, 0);

	if (n != 0) {
		snprintf(line, sizeof(line), "kern.hakios.pcie: %s", strerror(errno));
		printf("pcie_report: %s\n", line);
		write_file("/private/var/pcie.txt", line);
		write_file("/private/var/mobile/tmp/pcie.txt", line);
		write_file("/private/var/root/pcie.txt", line);
		return 1;
	}
	if (len == 0 || buf[0] == 0) {
		line[0] = 0;
		strcpy(line, "kern.hakios.pcie is empty: the driver has not run (pcie=1?)");
		printf("pcie_report: %s\n", line);
		write_file("/private/var/pcie.txt", line);
		write_file("/private/var/mobile/tmp/pcie.txt", line);
		write_file("/private/var/root/pcie.txt", line);
		return 0;
	}

	snprintf(line, sizeof(line), "%s", buf);
	printf("pcie_report: %s\n", line);
	write_file("/private/var/pcie.txt", line);
		write_file("/private/var/mobile/tmp/pcie.txt", line);
		write_file("/private/var/root/pcie.txt", line);
	return 0;
}
