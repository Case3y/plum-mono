#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# /////////////////////////////////////////////////////////////////
#
#  Usage: python build_bolder.py [ttf|woff|woff2|all]
#                            (--alt none|all|<label>[,<label>...])
#                            (--suffix SUF[,SUF...]) (--amount N)
#                            (--no-embolden) (--install-deps)
#
#  This is build.py with two changes:
#
#  1. No ttfautohint: the ttf files are built unhinted.
#
#  2. After fontmake compiles the UFO sources, the Regular and Italic
#     outlines are lightly emboldened (FontForge changeWeight, the same
#     operation comic-mono uses to derive its bold).  Bold and
#     BoldItalic are never touched; the family stays a 4-style
#     R/B/I/BI family with usWeightClass 400 -- this REPLACES the
#     regular weight, it does not add a new one.
#
#  Alt-glyph variants: source/alt-glyphs/<glyph>-<label>/<weight>/<glyph>.glif
#  holds a drop-in replacement for <glyph> in that weight -- the part before
#  the first "-" is the glyph being replaced, the part after is the variant
#  label used to pick it with --alt.  A build overlays every folder whose
#  label it selects onto a copy of the master UFOs (in gen/<family>/,
#  generated -- never hand-edit) and renames the family.  source/ is the
#  single hand-maintained source and is never modified.
#
#  The family-name suffix is specified explicitly with --suffix (default
#  "Custom"), matched to the selected variants in order; the unmodified
#  master keeps the bare family name.
#
#    --alt none                          unmodified family   "Plum Mono"
#    --alt dotted                        the dotted variant  "Plum Mono Custom"
#    --alt dotted --suffix SlashedZero   "Plum Mono SlashedZero"
#    --alt dotted,foo --suffix One,Two   two variants, two suffixes
#    --alt all                           base + every variant (default)
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
#  Output layout (PlumMono[-SUF] is the family name without spaces):
#    gen/PlumMono[-SUF]/           generated variant sources (do not edit)
#    build/ttf/PlumMono[-SUF]/     unhinted ttf files
#    build/web/PlumMono[-SUF]/     woff + woff2
#
#  Dependencies (conda activate develop):
#    fontmake, fonttools, zopfli, brotli (pip)
#    ffpython (FontForge's Python; emboldening only)
#
#  NOTE: woff and woff2 builds require that you build the ttf files
#        first (python build_bolder.py ttf).  They convert the ttf
#        builds, not the UFO source files.
#
# /////////////////////////////////////////////////////////////////

import argparse
import importlib.util
import plistlib
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

# The four Plum Mono variants in upstream build order
VARIANTS = ("Regular", "Bold", "Italic", "BoldItalic")

# alt-glyphs weight folder for each build variant
WEIGHT_DIR = {
    "Regular": "regular",
    "Bold": "bold",
    "Italic": "italic",
    "BoldItalic": "bolditalic",
}

REPO_ROOT = Path(__file__).resolve().parent
MASTER_TTF = REPO_ROOT / "master_ttf"
GEN_SRC = REPO_ROOT / "gen"
ALT_GLYPHS = REPO_ROOT / "source" / "alt-glyphs"

# --- alt-glyph variants ---------------------------------------------------
# The unmodified master is built as-is; an alt-glyph variant builds a family
# with an explicit --suffix appended to the name, so they can be installed
# side by side.
BASE_FAMILY = "Plum Mono"    # family name of the unmodified master
BASE_PS = "PlumMono"         # PostScript / output name stem of the master
DEFAULT_SUFFIX = "Custom"    # --suffix default for alt-glyph variants


def family_name(suffix):
    return BASE_FAMILY if not suffix else f"{BASE_FAMILY} {suffix}"


def ps_stem(suffix):
    """PostScript name stem: no spaces, no hyphens (hyphen separates style)."""
    return BASE_PS + "".join(c for c in suffix if c.isalnum())


def name_token(suffix):
    """Output folder name and ttf file stem: the family name without spaces."""
    if not suffix:
        return BASE_PS
    return f"{BASE_PS}-{'-'.join(suffix.split())}"


def web_token(suffix):
    return name_token(suffix).lower()


def ttf_dir(suffix):
    return REPO_ROOT / "build" / "ttf" / name_token(suffix)


def web_dir(suffix):
    return REPO_ROOT / "build" / "web" / name_token(suffix)


def ttf_name(suffix, variant):
    return f"{name_token(suffix)}-{variant}.ttf"


def web_name(suffix, variant, ext):
    return f"{web_token(suffix)}-{variant.lower()}.{ext}"


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
# Alt-glyph variants (single master -> gen/<family>/)
# ----------------------------------------------------------------------

def discover_labels():
    """Every variant label found under source/alt-glyphs (the part after the
    first "-" of each <glyph>-<label> folder)."""
    if not ALT_GLYPHS.is_dir():
        return []
    labels = set()
    for entry in ALT_GLYPHS.iterdir():
        if entry.is_dir():
            if "-" not in entry.name:
                fail(f"source/alt-glyphs/{entry.name} must be named "
                     "'<glyph>-<label>' (glyph to replace, then the label).")
            labels.add(entry.name.split("-", 1)[1])
    return sorted(labels)


def resolve_selection(alt_value, suffix_value):
    """Turn --alt / --suffix into [(label, suffix), ...] to build, where
    label None means the unmodified master (always built with no suffix)."""
    labels = discover_labels()
    if alt_value == "all":
        selected = [None, *labels]
    elif alt_value == "none":
        selected = [None]
    else:
        selected = [item.strip() for item in alt_value.split(",") if item.strip()]
        unknown = [item for item in selected if item not in labels]
        if unknown:
            available = ", ".join(labels) if labels else "(none found)"
            fail(f"unknown alt-glyph label(s): {', '.join(unknown)}.  "
                 f"Available: {available}")

    suffixes = [item.strip() for item in suffix_value.split(",")] \
        if suffix_value.strip() else []
    selection = []
    index = 0
    for label in selected:
        if label is None:
            selection.append((None, ""))
            continue
        suffix = suffixes[index] if index < len(suffixes) else DEFAULT_SUFFIX
        index += 1
        selection.append((label, suffix))

    tokens = [name_token(suffix) for _label, suffix in selection]
    clashes = sorted({t for t in tokens if tokens.count(t) > 1})
    if clashes:
        fail("variants share the same output name "
             f"({', '.join(clashes)}); give distinct --suffix values.")
    return selection


def collect_overlays(label):
    """Map each build variant to {glyph name: replacement glif} for this label
    (empty for the base variant)."""
    overlays = {variant: {} for variant in VARIANTS}
    if label is None:
        return overlays
    for entry in sorted(ALT_GLYPHS.iterdir()):
        if not entry.is_dir() or "-" not in entry.name:
            continue
        glyph, entry_label = entry.name.split("-", 1)
        if entry_label != label:
            continue
        for variant in VARIANTS:
            glif = entry / WEIGHT_DIR[variant] / f"{glyph}.glif"
            if not glif.is_file():
                fail(f"{entry.name}: expected a replacement at "
                     f"{WEIGHT_DIR[variant]}/{glyph}.glif")
            overlays[variant][glyph] = glif
    return overlays


def materialize_variant(label, suffix):
    """Copy the master UFOs into gen/<family>/ and overlay this variant's
    alt-glyph replacements (none for the base variant)."""
    overlays = collect_overlays(label)
    root = GEN_SRC / name_token(suffix)
    if root.is_dir():
        remove_dir(root)
    root.mkdir(parents=True)

    for variant in VARIANTS:
        master = REPO_ROOT / "source" / f"PlumMono-{variant}.ufo"
        target = root / f"PlumMono-{variant}.ufo"
        shutil.copytree(master, target)
        for glyph, glif in overlays[variant].items():
            overlay_glyph(target, glyph, glif)
        if suffix:
            rename_family(target / "fontinfo.plist", suffix, variant)

    print(f"generated {family_name(suffix)} variant sources in {root}")
    return root


def overlay_glyph(ufo, glyph, alt_glif_path):
    """Replace the outline of <glyph> in the copied UFO with the alt glif's,
    keeping the master's name, Unicode mapping, advance width and lib."""
    glyph_file = ufo / "glyphs" / f"{glyph}.glif"
    if not glyph_file.is_file():
        fail(f"{alt_glif_path} replaces '{glyph}', but {ufo.name} has no "
             f"glyphs/{glyph}.glif.")

    master_text = glyph_file.read_text(encoding="utf-8")
    alt_text = alt_glif_path.read_text(encoding="utf-8")

    alt_name = re.search(r'<glyph name="([^"]*)"', alt_text)
    if not alt_name or alt_name.group(1) != glyph:
        found = alt_name.group(1) if alt_name else "?"
        fail(f"{alt_glif_path}: glyph name is '{found}', expected '{glyph}'.")

    # the monospace advance must not change
    master_width = re.search(r'<advance[^>]*width="([^"]*)"', master_text)
    alt_width = re.search(r'<advance[^>]*width="([^"]*)"', alt_text)
    master_width = master_width.group(1) if master_width else None
    alt_width = alt_width.group(1) if alt_width else None
    if alt_width != master_width:
        fail(f"{alt_glif_path}: advance width {alt_width} does not match "
             f"{glyph} ({master_width}) -- the monospace layout must not change.")

    outline_re = re.compile(r"<outline>.*?</outline>", re.S)
    alt_outline = outline_re.search(alt_text)
    master_outline = outline_re.search(master_text)
    if master_outline:
        replacement = alt_outline.group(0) if alt_outline else ""
        master_text = (master_text[:master_outline.start()] + replacement +
                       master_text[master_outline.end():])
    elif alt_outline:
        master_text = master_text.replace(
            "</glyph>", f"  {alt_outline.group(0)}\n</glyph>", 1)
    glyph_file.write_text(master_text, encoding="utf-8", newline="")


def rename_family(fontinfo_path, suffix, variant):
    """Give the variant a suffix-specific family so it can be installed
    alongside the base family."""
    family = family_name(suffix)
    ps_name = f"{ps_stem(suffix)}-{variant}"
    fontinfo = plistlib.loads(fontinfo_path.read_bytes())
    style_name = fontinfo.get("styleName", variant)
    fontinfo["familyName"] = family
    fontinfo["styleMapFamilyName"] = family
    fontinfo["postscriptFontName"] = ps_name
    fontinfo["postscriptFullName"] = f"{family} {style_name}"
    fontinfo["openTypeNamePreferredFamilyName"] = family
    fontinfo["openTypeNameCompatibleFullName"] = f"{family} {style_name}"
    fontinfo["openTypeNameUniqueID"] = f"{ps_name}: 2026"
    fontinfo_path.write_bytes(plistlib.dumps(fontinfo, sort_keys=False))


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

def build_ttf(selection, amount, embolden):
    confirm_dependencies(require_ffpython=(embolden and amount > 0))

    print(" ")
    print("Starting build...")
    print(" ")

    for label, suffix in selection:
        src_root = materialize_variant(label, suffix)
        clean_master_ttf()

        out_dir = ttf_dir(suffix)
        # reset the output folder (also drops any legacy flat ttf layout)
        if out_dir.is_dir():
            remove_dir(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        for variant in VARIANTS:
            run_fontmake(src_root / f"PlumMono-{variant}.ufo")

        if embolden and amount > 0:
            embolden_light_weights(amount)

        apply_postbuild_fixes()

        print(" ")
        for variant in VARIANTS:
            target = out_dir / ttf_name(suffix, variant)
            shutil.copy2(MASTER_TTF / f"PlumMono-{variant}.ttf", target)
            print(f"{family_name(suffix)} {variant} ttf build path: {target}")

        remove_dir(MASTER_TTF)


def require_ttf_builds(suffix):
    missing = [v for v in VARIANTS
               if not (ttf_dir(suffix) / ttf_name(suffix, v)).is_file()]
    if missing:
        fail(f"{family_name(suffix)} ttf build(s) not found for: "
             f"{', '.join(missing)}.  Build the ttf files first with "
             "'python build_bolder.py ttf'.")


def build_woff(selection):
    for _label, suffix in selection:
        require_ttf_builds(suffix)
    enable_zopfli_woff()
    print("Beginning web font build with fontTools + zopfli")
    for _label, suffix in selection:
        out_dir = web_dir(suffix)
        out_dir.mkdir(parents=True, exist_ok=True)
        for variant in VARIANTS:
            ttf_path = ttf_dir(suffix) / ttf_name(suffix, variant)
            woff_path = out_dir / web_name(suffix, variant, "woff")
            try:
                convert_web_font(ttf_path, woff_path, "woff")
            except OSError as error:
                fail(f"Failed to build {woff_path.name} from {ttf_path.name}: {error}")
            print(f"{family_name(suffix)} {variant} woff set successfully built "
                  f"from {ttf_path.name}")
        print(" ")
        for variant in VARIANTS:
            print(f"{family_name(suffix)} {variant} woff build path: "
                  f"{out_dir / web_name(suffix, variant, 'woff')}")


def build_woff2(selection):
    try:
        import brotli  # noqa: F401
    except ImportError:
        fail("The brotli library was not found.  Install it with "
             "'pip install brotli', then attempt your build again.")
    for _label, suffix in selection:
        require_ttf_builds(suffix)
    print("Beginning web font build with fontTools + brotli")
    for _label, suffix in selection:
        out_dir = web_dir(suffix)
        out_dir.mkdir(parents=True, exist_ok=True)
        for variant in VARIANTS:
            ttf_path = ttf_dir(suffix) / ttf_name(suffix, variant)
            woff2_path = out_dir / web_name(suffix, variant, "woff2")
            try:
                convert_web_font(ttf_path, woff2_path, "woff2")
            except OSError as error:
                fail(f"Failed to build woff2 from {ttf_path.name}: {error}")
            print(f"{family_name(suffix)} {variant} woff2 set successfully built "
                  f"from {ttf_path.name}")
        print(" ")
        for variant in VARIANTS:
            print(f"{family_name(suffix)} {variant} woff2 build path: "
                  f"{out_dir / web_name(suffix, variant, 'woff2')}")


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
    parser.add_argument("--alt", default="all",
                        help="alt-glyph variant(s) to build: a label, a "
                             "comma-separated list, 'all' (base + every "
                             "variant) or 'none' (base only); default all")
    parser.add_argument("--suffix", default="",
                        help="family-name suffix for the alt-glyph variants, "
                             "matched to the selected variants in order "
                             "(comma-separated for several); "
                             f"default {DEFAULT_SUFFIX!r}")
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
    selection = resolve_selection(args.alt, args.suffix)

    if args.install_deps:
        install_deps()
        return

    if args.target == "ttf":
        build_ttf(selection, args.amount, embolden)
    elif args.target == "woff":
        build_woff(selection)
    elif args.target == "woff2":
        build_woff2(selection)
    elif args.target == "all":
        build_ttf(selection, args.amount, embolden)
        build_woff(selection)
        build_woff2(selection)


if __name__ == "__main__":
    main()
