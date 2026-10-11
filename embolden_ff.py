#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Embolden a TTF with FontForge's changeWeight (run under ffpython).

Usage: ffpython embolden_ff.py <in.ttf> <out.ttf> <amount>

Only the outlines matter in the output: build_new.py transplants the
glyph shapes back into the original TTF (which keeps GPOS/GSUB/GDEF
intact), because FontForge's binary round trip is not table-faithful.
"""

import sys

import fontforge


def main():
    in_path, out_path, amount = sys.argv[1], sys.argv[2], float(sys.argv[3])
    font = fontforge.open(in_path)
    # changeWeight only affects the current selection -- without this
    # it silently does nothing (comic-mono's script does the same)
    font.selection.all()
    # same call as comic-mono's generate script; "squish" compresses
    # counters so the monospace advance can stay untouched
    font.changeWeight(amount, "LCG", 0, 0, "squish")
    font.generate(out_path)
    print("emboldened by %g -> %s" % (amount, out_path))


if __name__ == "__main__":
    main()
