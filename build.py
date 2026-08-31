#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# /////////////////////////////////////////////////////////////////
#
#  Usage: python build.py [ttf|woff|woff2|subsets|all] (--install-deps)
#
#  Output layout:
#    build/ttf/hint/     ttfautohint-hinted ttf files
#    build/ttf/unhint/   ttf files without ttfautohint hinting
#    build/web/fonts/    woff + woff2 (complete and subset sets)
#
#  Dependencies (conda activate develop):
#    fontmake, fonttools, zopfli, brotli (pip)
#    ttfautohint executable (the ttfautohint-py bundled build is preferred)
#
#  NOTE: woff and woff2 builds require that you build the ttf files
#        first (python build.py ttf).  They convert the hinted ttf
#        builds, not the UFO source files.
#
# /////////////////////////////////////////////////////////////////

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

# ttfautohint local install path from ttfautohint-build.sh (upstream default
# location).  This is revised to ttfautohint on the user's PATH if the local
# install is not identified.
TTFAH_LOCAL = Path.home() / "ttfautohint-build" / "local" / "bin" / "ttfautohint"

# The four Plum Mono variants in upstream build order, mapped to their
# ttfautohint -H (hinting range min) values from build-ttf.sh / build-subsets.sh
VARIANTS = {
    "Regular": "181",
    "Bold": "260",
    "Italic": "145",
    "BoldItalic": "265",
}

# ttfautohint flags shared by the ttf and subsets builds (verbatim from upstream)
TTFAH_FLAGS = ["-l", "6", "-r", "50", "-x", "10", "-D", "latn", "-f", "latn",
               "-a", "qsq", "-W", "-t", "-X", "", "-I"]

REPO_ROOT = Path(__file__).resolve().parent
MASTER_TTF = REPO_ROOT / "master_ttf"
TTF_BUILD = REPO_ROOT / "build" / "ttf"
HINT_TTF = TTF_BUILD / "hint"      # ttfautohint-hinted ttf files
UNHINT_TTF = TTF_BUILD / "unhint"  # ttf files without ttfautohint hinting
WEB_BUILD = REPO_ROOT / "build" / "web" / "fonts"
TEMP_SOURCE = REPO_ROOT / "source" / "temp"

# web font output names (lowercase: plummono-<style>[-subset].woff[2])
WEB_NAMES = {
    "Regular": "plummono-regular",
    "Bold": "plummono-bold",
    "Italic": "plummono-italic",
    "BoldItalic": "plummono-bolditalic",
}


def fail(message):
    print(f"❌ {message}", file=sys.stderr)
    sys.exit(1)


def find_ttfautohint():
    # Prefer the ttfautohint executable bundled with the ttfautohint-py wheel:
    # the official ttfautohint 1.8.4 Windows build cannot load -R reference
    # fonts at all ("unknown file format"), which the subsets build requires.
    bundled_name = "ttfautohint.exe" if sys.platform == "win32" else "ttfautohint"
    try:
        import ttfautohint as ttfa_py
        bundled = Path(ttfa_py.__file__).parent / bundled_name
        if bundled.is_file() and os.access(bundled, os.X_OK):
            return str(bundled)
    except ImportError:
        pass
    if shutil.which("ttfautohint"):
        return "ttfautohint"
    if TTFAH_LOCAL.is_file():
        return str(TTFAH_LOCAL)
    return None


def confirm_dependencies(require_ttfautohint=True):
    print("Confirming that build dependencies are installed...")
    print(" ")
    problems = []
    if not shutil.which("fontmake"):
        problems.append("fontmake was not found.  Install it with "
                        "'pip install fontmake', then attempt your build again.")
    if importlib.util.find_spec("fontTools") is None:
        problems.append("The fontTools library was not found.  Install it with "
                        "'pip install fonttools', then attempt your build again.")
    ttfa = find_ttfautohint()
    if require_ttfautohint and ttfa is None:
        problems.append("ttfautohint was not found (neither on your PATH nor at "
                        f"{TTFAH_LOCAL}).  Install the official ttfautohint build, "
                        "then attempt your build again.")
    if require_ttfautohint and ttfa is not None:
        print("ttfautohint executable identified")
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        print("Build canceled.", file=sys.stderr)
        sys.exit(1)
    return ttfa


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


def run_fontmake(ufo_path, subset=False):
    """Build one UFO source to a ttf in master_ttf/ (fontmake's default output
    directory for static ttf builds)."""
    command = [shutil.which("fontmake")]
    if subset:
        command.append("--subset")
    command += ["-u", str(ufo_path), "-o", "ttf"]
    result = subprocess.run(command, cwd=REPO_ROOT)
    if result.returncode != 0:
        fail(f"Unable to build the {ufo_path.name} variant set.  Build canceled.")


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
# Hinting (ttfautohint)
# ----------------------------------------------------------------------

def hint_ttf(ttfa, ttf_path, subset=False):
    variant = ttf_path.stem.replace("PlumMono-", "")
    hinted_dir = MASTER_TTF / "hinted"
    hinted_dir.mkdir(exist_ok=True)
    control_file = REPO_ROOT / "tt-hinting" / f"PlumMono-{variant}-TA.txt"
    command = [ttfa, *TTFAH_FLAGS, "-H", VARIANTS[variant]]
    if subset:
        # upstream build-subsets.sh uses the regular set as the x-height reference
        command += ["-R", str(MASTER_TTF / "PlumMono-Regular.ttf")]
    command += ["-m", str(control_file), str(ttf_path), str(hinted_dir / ttf_path.name)]
    result = subprocess.run(command, cwd=REPO_ROOT)
    if result.returncode != 0:
        kind = "variant subset" if subset else "variant set"
        fail(f"Unable to execute ttfautohint on the PlumMono-{variant} {kind}.  Build canceled.")
    suffix = " subset" if subset else ""
    print(f"master_ttf/{ttf_path.name}{suffix} - successful hinting with ttfautohint")


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

def build_ttf():
    ttfa = confirm_dependencies()
    clean_master_ttf()

    print(" ")
    print("Starting build...")
    print(" ")

    # reset the output folders (and drop legacy flat ttf files from old builds)
    for folder in (HINT_TTF, UNHINT_TTF):
        if folder.is_dir():
            remove_dir(folder)
        folder.mkdir(parents=True, exist_ok=True)
    for legacy in TTF_BUILD.glob("PlumMono-*.ttf"):
        legacy.unlink()

    for variant in VARIANTS:
        ufo_path = REPO_ROOT / "source" / f"PlumMono-{variant}.ufo"
        run_fontmake(ufo_path)

    apply_postbuild_fixes()

    # unhinted set: the fixed master files, before ttfautohint processing
    for variant in VARIANTS:
        shutil.copy2(MASTER_TTF / f"PlumMono-{variant}.ttf",
                     UNHINT_TTF / f"PlumMono-{variant}.ttf")

    print(" ")
    print("Attempting ttfautohint hinting...")
    print(" ")
    for variant in VARIANTS:
        hint_ttf(ttfa, MASTER_TTF / f"PlumMono-{variant}.ttf")

    print(" ")
    for variant in VARIANTS:
        shutil.move(str(MASTER_TTF / "hinted" / f"PlumMono-{variant}.ttf"),
                    str(HINT_TTF / f"PlumMono-{variant}.ttf"))
        print(f"{variant} unhinted ttf build path: {UNHINT_TTF / f'PlumMono-{variant}.ttf'}")
        print(f"{variant} hinted ttf build path: {HINT_TTF / f'PlumMono-{variant}.ttf'}")

    remove_dir(MASTER_TTF)


def require_ttf_builds():
    missing = [v for v in VARIANTS if not (HINT_TTF / f"PlumMono-{v}.ttf").is_file()]
    if missing:
        fail(f"hinted ttf build(s) not found for: {', '.join(missing)}.  "
             "Build the ttf files first with 'python build.py ttf'.")


def build_woff():
    require_ttf_builds()
    enable_zopfli_woff()
    print("Beginning web font build with fontTools + zopfli")
    WEB_BUILD.mkdir(parents=True, exist_ok=True)
    for variant in VARIANTS:
        ttf_path = HINT_TTF / f"PlumMono-{variant}.ttf"
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
        ttf_path = HINT_TTF / f"PlumMono-{variant}.ttf"
        woff2_path = WEB_BUILD / f"{WEB_NAMES[variant]}.woff2"
        try:
            convert_web_font(ttf_path, woff2_path, "woff2")
        except OSError as error:
            fail(f"Failed to build woff2 from {ttf_path.name}: {error}")
        print(f"{variant} woff2 set successfully built from {ttf_path.name}")
    print(" ")
    for variant in VARIANTS:
        print(f"{variant} woff2 build path: {WEB_BUILD / f'{WEB_NAMES[variant]}.woff2'}")


def build_subsets():
    ttfa = confirm_dependencies()
    clean_master_ttf()

    # create temporary source files with lib.plist replacements that include
    # the subset definitions from source/subset-lib
    if TEMP_SOURCE.exists():
        shutil.rmtree(TEMP_SOURCE)
    TEMP_SOURCE.mkdir()

    subset_lib = REPO_ROOT / "source" / "subset-lib"
    for variant in VARIANTS:
        temp_ufo = TEMP_SOURCE / f"PlumMono-{variant}.ufo"
        shutil.copytree(REPO_ROOT / "source" / f"PlumMono-{variant}.ufo", temp_ufo)
        shutil.copy2(subset_lib / f"lib-{variant.lower()}.plist", temp_ufo / "lib.plist")

    print("Starting web font subset build...")
    print(" ")
    for variant in VARIANTS:
        run_fontmake(TEMP_SOURCE / f"PlumMono-{variant}.ufo", subset=True)

    apply_postbuild_fixes()

    print(" ")
    print("Attempting ttfautohint hinting...")
    print(" ")
    for variant in VARIANTS:
        hint_ttf(ttfa, MASTER_TTF / f"PlumMono-{variant}.ttf", subset=True)
    print(" ")

    enable_zopfli_woff()
    WEB_BUILD.mkdir(parents=True, exist_ok=True)

    # NOTE: upstream build-subsets.sh converts the unhinted master_ttf files
    # (the hinted copies in master_ttf/hinted are never used) - replicated here
    for variant in VARIANTS:
        ttf_path = MASTER_TTF / f"PlumMono-{variant}.ttf"
        try:
            convert_web_font(ttf_path, WEB_BUILD / f"{WEB_NAMES[variant]}-subset.woff", "woff")
        except OSError as error:
            fail(f"Failed to build woff subset from {ttf_path.name}: {error}")
        print(f"{variant} woff subset successfully built from {ttf_path.name}")
    print(" ")
    for variant in VARIANTS:
        ttf_path = MASTER_TTF / f"PlumMono-{variant}.ttf"
        try:
            convert_web_font(ttf_path, WEB_BUILD / f"{WEB_NAMES[variant]}-subset.woff2", "woff2")
        except OSError as error:
            fail(f"Failed to build woff2 subset from {ttf_path.name}: {error}")
        print(f"{variant} woff2 font subset successfully built from {ttf_path.name}")

    print(" ")
    print("Moving web font subset files to build directory...")
    for variant in VARIANTS:
        print(f"{variant} woff build path: {WEB_BUILD / f'{WEB_NAMES[variant]}-subset.woff'}")
        print(f"{variant} woff2 build path: {WEB_BUILD / f'{WEB_NAMES[variant]}-subset.woff2'}")

    remove_dir(MASTER_TTF)
    remove_dir(TEMP_SOURCE)


def install_deps():
    print("Installing Python build dependencies with pip...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade",
                    "fontmake", "fonttools", "zopfli", "brotli"], check=False)
    print(" ")
    print("NOTE: the ttfautohint executable cannot be installed with pip.")
    print("Install it from https://www.freetype.org/ttfautohint/ (official")
    print("Windows builds available) and make sure ttfautohint(.exe) is on")
    print("your PATH before building.")


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
	        description="Python build pipeline for the Plum Mono typeface "
                    "(port of build-ttf.sh / build-woff.sh / build-woff2.sh / build-subsets.sh).")
    parser.add_argument("target", nargs="?", default="all",
                        choices=["ttf", "woff", "woff2", "subsets", "all"],
                        help="build target (default: all = ttf + woff + woff2 + subsets)")
    parser.add_argument("--install-deps", action="store_true",
                        help="install the Python build dependencies with pip, then exit")
    args = parser.parse_args()

    if args.install_deps:
        install_deps()
        return

    if args.target == "ttf":
        build_ttf()
    elif args.target == "woff":
        build_woff()
    elif args.target == "woff2":
        build_woff2()
    elif args.target == "subsets":
        build_subsets()
    elif args.target == "all":
        build_ttf()
        build_woff()
        build_woff2()
        build_subsets()


if __name__ == "__main__":
    main()
