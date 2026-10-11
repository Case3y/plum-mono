#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# /////////////////////////////////////////////////////////////////
#
#  Usage: python build_latest.py [ttf|woff|woff2|all]
#                            (--amount N) (--no-embolden) (--install-deps)
#
#  This is build.py with two changes:
#
#  1. No ttfautohint: the ttf files are built unhinted and saved
#     directly in build/ttf/ (no hint/unhint split).
#
#  2. After fontmake compiles the UFO sources, the Regular and Italic
#     outlines are lightly emboldened (FontForge changeWeight, the same
#     operation comic-mono uses to derive its bold).  Bold and
#     BoldItalic are never touched; the family stays a 4-style
#     R/B/I/BI family with usWeightClass 400 -- this REPLACES the
#     regular weight, it does not add a new one.
#
#  Emboldening pipeline (per light variant):
#    fontmake (unhinted ttf, full OpenType tables)
#      -> ffpython embolden_ff.py <amount>     (outlines only)
#      -> fontTools transplant by glyph name   (tables preserved)
#      -> postbuild fixes                      (as in build.py)
#
#  FontForge is used ONLY to compute the emboldened outlines: its
#  binary round trip reorders glyphs and cannot be trusted with
#  GPOS, so the emboldened glyf/hmtx are transplanted by glyph NAME
#  back into the fontmake-built ttf, whose GPOS/GSUB/GDEF/cmap/name/
#  OS/2/post tables survive byte-identical (verified on every run).
#
#  Output layout:
#    build/ttf/          unhinted ttf files
#    build/web/fonts/    woff + woff2
#
#  Dependencies (conda activate develop):
#    fontmake, fonttools, zopfli, brotli (pip)
#    ffpython (FontForge's Python; emboldening only)
#
#  NOTE: woff and woff2 builds require that you build the ttf files
#        first (python build_latest.py ttf).  They convert the ttf
#        builds, not the UFO source files.
#
# /////////////////////////////////////////////////////////////////

import argparse
import importlib.util
import shutil
import subprocess
import sys
import time
from pathlib import Path

# The four Plum Mono variants in upstream build order
VARIANTS = ("Regular", "Bold", "Italic", "BoldItalic")

REPO_ROOT = Path(__file__).resolve().parent
MASTER_TTF = REPO_ROOT / "master_ttf"
TTF_BUILD = REPO_ROOT / "build" / "ttf"
WEB_BUILD = REPO_ROOT / "build" / "web" / "fonts"

# web font output names (lowercase: plummono-<style>.woff[2])
WEB_NAMES = {
    "Regular": "plummono-regular",
    "Bold": "plummono-bold",
    "Italic": "plummono-italic",
    "BoldItalic": "plummono-bolditalic",
}

# --- emboldening configuration -------------------------------------------

# the light weights that get emboldened; Bold / BoldItalic are never touched
EMBOLDEN_VARIANTS = ("Regular", "Italic")

# emboldening amount in font units at 2048 UPM:
#   H stem 207 -> 232 (+12%), just under a typical Medium (+10..13%)
DEFAULT_AMOUNT = 25.0

# ffpython locations (FontForge's Python interpreter)
FFPYTHON_CANDIDATES = [
    shutil.which("ffpython"),
    r"C:\Program Files (x86)\FontForgeBuilds\bin\ffpython.exe",
    r"C:\Program Files\FontForge\bin\ffpython.exe",
]


def fail(message):
    print(f"❌ {message}", file=sys.stderr)
    sys.exit(1)


def find_ffpython():
    for candidate in FFPYTHON_CANDIDATES:
        if candidate and Path(candidate).exists():
            return str(candidate)
    return None


def confirm_dependencies(require_ffpython=False):
    print("Confirming that build dependencies are installed...")
    print(" ")
    problems = []
    if not shutil.which("fontmake"):
        problems.append("fontmake was not found.  Install it with "
                        "'pip install fontmake', then attempt your build again.")
    if importlib.util.find_spec("fontTools") is None:
        problems.append("The fontTools library was not found.  Install it with "
                        "'pip install fonttools', then attempt your build again.")
    ffpython = find_ffpython()
    if require_ffpython and ffpython is None:
        problems.append("ffpython was not found (FontForge's Python interpreter). "
                        "Install FontForge, then attempt your build again.")
    if require_ffpython and ffpython is not None:
        print(f"ffpython executable identified: {ffpython}")
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        print("Build canceled.", file=sys.stderr)
        sys.exit(1)
    return ffpython


def remove_dir(path):
    """Remove a directory tree, retrying briefly: on Windows a freshly
    written file may stay locked for a moment (e.g. antivirus scanning),
    which must not fail an otherwise successful build."""
    for attempt in range(4):
        try:
            shutil.rmtree(path)
            return
        except (PermissionError, OSError):
            if attempt == 3:
                print(f"⚠️  Could not remove temporary directory {path} "
                      "(locked by another program); remove it manually.",
                      file=sys.stderr)
                return
            time.sleep(1.0)


def clean_master_ttf():
    if MASTER_TTF.is_dir():
        remove_dir(MASTER_TTF)


def run_fontmake(ufo_path):
    """Build one UFO source to a ttf in master_ttf/ (fontmake's default output
    directory for static ttf builds)."""
    command = [shutil.which("fontmake")]
    command += ["-u", str(ufo_path), "-o", "ttf"]
    result = subprocess.run(command, cwd=REPO_ROOT)
    if result.returncode != 0:
        fail(f"Unable to build the {ufo_path.name} variant set.  Build canceled.")


# ----------------------------------------------------------------------
# Light-weight emboldening (FontForge changeWeight + fontTools transplant)
# ----------------------------------------------------------------------

def embolden_outlines(ffpython, in_ttf, out_ttf, amount):
    """Embolden a ttf with FontForge's changeWeight (run under ffpython).

    Only the outlines of the output matter: FontForge's ttf round trip
    reorders glyphs and cannot be trusted with GPOS, so the result is
    transplanted back by glyph name afterwards."""
    result = subprocess.run(
        [ffpython, str(REPO_ROOT / "embolden_ff.py"),
         str(in_ttf), str(out_ttf), str(amount)],
        capture_output=True, text=True, cwd=REPO_ROOT)
    if result.returncode != 0 or not out_ttf.exists():
        print(result.stdout[-2000:], file=sys.stderr)
        print(result.stderr[-2000:], file=sys.stderr)
        fail(f"Unable to embolden {in_ttf.name} with FontForge.  Build canceled.")


def transplant_outlines(orig_ttf, emboldened_ttf, out_ttf, work_dir):
    """Copy the emboldened outlines into the fontmake-built ttf by glyph
    name, keeping every other table (GPOS/GSUB/GDEF/cmap/name/OS/2/post)
    intact."""
    from fontTools.ttLib import TTFont

    dst = TTFont(orig_ttf)           # full, correct tables
    src = TTFont(emboldened_ttf)     # FontForge output: outlines only
    names = dst.getGlyphOrder()
    missing = [n for n in names if n not in src["glyf"].glyphs]
    if missing:
        fail(f"FontForge lost glyphs from {emboldened_ttf.name}: "
             f"{missing[:5]} (+{len(missing) - 5} more).  Build canceled.")
    for n in names:
        dst["glyf"].glyphs[n] = src["glyf"].glyphs[n]
        width_orig, _lsb = dst["hmtx"][n]
        width_new, lsb_new = src["hmtx"][n]
        if width_new != width_orig:
            fail(f"Emboldening changed the advance of {n} in "
                 f"{emboldened_ttf.name} ({width_orig} -> {width_new}).  "
                 "The monospace layout must not change.  Build canceled.")
        dst["hmtx"].metrics[n] = (width_orig, lsb_new)
    dst.save(out_ttf)

    # ---- verification -------------------------------------------------
    # fontTools legitimately recalculates bounds (head/maxp/hhea) when the
    # outlines grow, so the transplanted font is compared against a clean
    # fontTools round trip of the ORIGINAL; any difference in the tables
    # below then means a real change.
    baseline = work_dir / (orig_ttf.stem + "-baseline.ttf")
    TTFont(orig_ttf).save(baseline)
    base = TTFont(baseline, lazy=True)
    new = TTFont(out_ttf, lazy=True)
    if base.getGlyphOrder() != new.getGlyphOrder():
        fail(f"Transplanting {out_ttf.name} changed the glyph order.  Build canceled.")
    if base.getBestCmap() != new.getBestCmap():
        fail(f"Transplanting {out_ttf.name} changed the cmap.  Build canceled.")
    for table in ("GPOS", "GSUB", "GDEF", "cmap", "name", "OS/2", "post"):
        if base.reader[table] != new.reader[table]:
            fail(f"Transplanting {out_ttf.name} changed the {table} table.  "
                 "Build canceled.")
    base.close()
    new.close()
    baseline.unlink()
    print(f"{out_ttf.name} - successful emboldening "
          f"(GPOS GSUB GDEF cmap name OS/2 post verified identical)")


def embolden_light_weights(amount):
    """Embolden the Regular and Italic masters in place (master_ttf/),
    after fontmake and before the postbuild fixes."""
    ffpython = confirm_dependencies(require_ffpython=True)
    work_dir = MASTER_TTF / "embolden-work"
    work_dir.mkdir(exist_ok=True)
    print(" ")
    print(f"Emboldening the light weights by {amount:g} font units "
          f"(H stem 207 -> ~232, just under a typical Medium)...")
    print(" ")
    for variant in EMBOLDEN_VARIANTS:
        ttf_path = MASTER_TTF / f"PlumMono-{variant}.ttf"
        emboldened = work_dir / f"emb-{variant}.ttf"
        embolden_outlines(ffpython, ttf_path, emboldened, amount)
        transplant_outlines(ttf_path, emboldened, ttf_path, work_dir)
    remove_dir(work_dir)


# ----------------------------------------------------------------------
# Post build fixes (inline ports of postbuild_processing/fixes/*.py)
# ----------------------------------------------------------------------

def fix_dsig(ttf_path):
    from fontTools import ttLib
    font = ttLib.TTFont(ttf_path)
    new_dsig = ttLib.newTable("DSIG")
    new_dsig.ulVersion = 1
    new_dsig.usFlag = 0
    new_dsig.usNumSigs = 0
    new_dsig.signatureRecords = []
    font.tables["DSIG"] = new_dsig
    font.save(ttf_path)
    print(f"{ttf_path} - successful DSIG table fix")


def fix_fstype(ttf_path):
    from fontTools.ttLib import TTFont
    font = TTFont(ttf_path)
    font["OS/2"].fsType = 0
    font.save(ttf_path)
    print(f"{ttf_path} - successful fstype fix")


def apply_postbuild_fixes():
    print(" ")
    print("Attempting DSIG table fixes with fontbakery...")
    print(" ")
    for ttf_path in sorted(MASTER_TTF.glob("*.ttf")):
        fix_dsig(ttf_path)
    print(" ")
    print("Attempting fstype fixes with fontbakery...")
    print(" ")
    for ttf_path in sorted(MASTER_TTF.glob("*.ttf")):
        fix_fstype(ttf_path)


# ----------------------------------------------------------------------
# Web font conversion (pure Python replacements for sfnt2woff-zopfli
# and woff2_compress)
# ----------------------------------------------------------------------

def enable_zopfli_woff():
    """Use zopfli (3 iterations) for WOFF 1.0 table compression, matching the
    upstream `sfnt2woff-zopfli -n 3` builds.  fontTools maps compression level
    2 to 3 zopfli iterations."""
    try:
        import zopfli  # noqa: F401
    except ImportError:
        return
    from fontTools.ttLib import sfnt
    sfnt.USE_ZOPFLI = True
    original_compress = sfnt.compress
    sfnt.compress = lambda data, level=2: original_compress(data, 2)


def convert_web_font(ttf_path, output_path, flavor):
    from fontTools.ttLib import TTFont
    font = TTFont(ttf_path)
    font.flavor = flavor
    font.save(output_path)


# ----------------------------------------------------------------------
# Build targets
# ----------------------------------------------------------------------

def build_ttf(amount, embolden):
    confirm_dependencies(require_ffpython=(embolden and amount > 0))
    clean_master_ttf()

    print(" ")
    print("Starting build...")
    print(" ")

    # reset the output folder (also drops the legacy hint/unhint layout and
    # flat ttf files from old builds)
    if TTF_BUILD.is_dir():
        remove_dir(TTF_BUILD)
    TTF_BUILD.mkdir(parents=True, exist_ok=True)

    for variant in VARIANTS:
        ufo_path = REPO_ROOT / "source" / f"PlumMono-{variant}.ufo"
        run_fontmake(ufo_path)

    if embolden and amount > 0:
        embolden_light_weights(amount)

    apply_postbuild_fixes()

    print(" ")
    for variant in VARIANTS:
        shutil.copy2(MASTER_TTF / f"PlumMono-{variant}.ttf",
                     TTF_BUILD / f"PlumMono-{variant}.ttf")
        print(f"{variant} ttf build path: {TTF_BUILD / f'PlumMono-{variant}.ttf'}")

    remove_dir(MASTER_TTF)


def require_ttf_builds():
    missing = [v for v in VARIANTS if not (TTF_BUILD / f"PlumMono-{v}.ttf").is_file()]
    if missing:
        fail(f"ttf build(s) not found for: {', '.join(missing)}.  "
             "Build the ttf files first with 'python build_latest.py ttf'.")


def build_woff():
    require_ttf_builds()
    enable_zopfli_woff()
    print("Beginning web font build with fontTools + zopfli")
    WEB_BUILD.mkdir(parents=True, exist_ok=True)
    for variant in VARIANTS:
        ttf_path = TTF_BUILD / f"PlumMono-{variant}.ttf"
        woff_path = WEB_BUILD / f"{WEB_NAMES[variant]}.woff"
        try:
            convert_web_font(ttf_path, woff_path, "woff")
        except OSError as error:
            fail(f"Failed to build {woff_path.name} from {ttf_path.name}: {error}")
        print(f"{variant} woff set successfully built from {ttf_path.name}")
    print(" ")
    for variant in VARIANTS:
        print(f"{variant} woff build path: {WEB_BUILD / f'{WEB_NAMES[variant]}.woff'}")


def build_woff2():
    require_ttf_builds()
    try:
        import brotli  # noqa: F401
    except ImportError:
        fail("The brotli library was not found.  Install it with "
             "'pip install brotli', then attempt your build again.")
    print("Beginning web font build with fontTools + brotli")
    WEB_BUILD.mkdir(parents=True, exist_ok=True)
    for variant in VARIANTS:
        ttf_path = TTF_BUILD / f"PlumMono-{variant}.ttf"
        woff2_path = WEB_BUILD / f"{WEB_NAMES[variant]}.woff2"
        try:
            convert_web_font(ttf_path, woff2_path, "woff2")
        except OSError as error:
            fail(f"Failed to build woff2 from {ttf_path.name}: {error}")
        print(f"{variant} woff2 set successfully built from {ttf_path.name}")
    print(" ")
    for variant in VARIANTS:
        print(f"{variant} woff2 build path: {WEB_BUILD / f'{WEB_NAMES[variant]}.woff2'}")


def install_deps():
    print("Installing Python build dependencies with pip...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade",
                    "fontmake", "fonttools", "zopfli", "brotli"], check=False)
    print(" ")
    print("NOTE: emboldening additionally requires FontForge's ffpython,")
    print("which is installed with FontForge from https://fontforge.org/.")


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
        description="Python build pipeline for the Plum Mono typeface "
                    "(unhinted builds + light-weight emboldening of "
                    "Regular/Italic).")
    parser.add_argument("target", nargs="?", default="all",
                        choices=["ttf", "woff", "woff2", "all"],
                        help="build target (default: all = ttf + woff + woff2)")
    parser.add_argument("--amount", type=float, default=DEFAULT_AMOUNT,
                        help="emboldening amount in font units at 2048 UPM; "
                             "H stem 207 -> 222/227/232/237 for 15/20/25/30 "
                             f"(default {DEFAULT_AMOUNT:g}, just under a Medium)")
    parser.add_argument("--no-embolden", action="store_true",
                        help="skip the emboldening step entirely "
                             "(build the original weights)")
    parser.add_argument("--install-deps", action="store_true",
                        help="install the Python build dependencies with pip, then exit")
    args = parser.parse_args()

    embolden = not args.no_embolden

    if args.install_deps:
        install_deps()
        return

    if args.target == "ttf":
        build_ttf(args.amount, embolden)
    elif args.target == "woff":
        build_woff()
    elif args.target == "woff2":
        build_woff2()
    elif args.target == "all":
        build_ttf(args.amount, embolden)
        build_woff()
        build_woff2()


if __name__ == "__main__":
    main()
