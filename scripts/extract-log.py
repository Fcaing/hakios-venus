#!/usr/bin/env python3
"""Pull the printable text out of a logdump image and report what is in it."""
import sys

src, dst = sys.argv[1], sys.argv[2]
d = open(src, "rb").read()

lines = []
for chunk in d.split(b"\n"):
    t = chunk.decode("utf-8", "replace")
    lines.append("".join(c if (32 <= ord(c) < 127 or c == "\t") else "." for c in t))

text = "\n".join(lines)
open(dst, "w", encoding="utf-8").write(text)

print("bytes %d | goodix %d | poke %d | event %d | panic %d | touch %d"
      % (len(d), text.count("goodix:"), text.count("ST FTS poke"),
         text.count("ST FTS event"), text.count("panic(cpu"), text.count("touch")))
