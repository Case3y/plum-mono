#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# /////////////////////////////////////////////////////////////////
#
#  Usage: python build.py [ttf|woff|woff2|all] (--install-deps)
#
#  Output layout:
#    build/ttf/          ttf files (unhinted)
#    build/web/fonts/    woff + woff2
#
#  Dependencies (conda activate develop):
#    fontmake, fonttools, zopfli, brotli (pip)
#
#  NOTE: woff and woff2 builds require that you build the ttf files
#        first (python build.py ttf).  They convert the ttf builds,
#        not the UFO source files.
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


def fail(message):
    print(f"❌ {message}", file=sys.stderr)
    sys.exit(1)


def confirm_dependencies():
    print("Confirming that build dependencies are installed...")
    print(" ")
    problems = []
    if not shutil.which("fontmake"):
        problems.append("fontmake was not found.  Install it with "
                        "'pip install fontmake', then attempt your build again.")
    if importlib.util.find_spec("fontTools") is None:
        problems.append("The fontTools library was not found.  Install it with "
                        "'pip install fonttools', then attempt your build again.")
    if problems:
        for problem in problems:
            print(problem, file=sys.stderr)
        print("Build canceled.", file=sys.stderr)
        sys.exit(1)


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

def build_ttf():
    confirm_dependencies()
    clean_master_ttf()

    print(" ")
    print("Starting build...")
    print(" ")

    # reset the output folder (also drops the legacy hint/unhint layout)
    if TTF_BUILD.is_dir():
        remove_dir(TTF_BUILD)
    TTF_BUILD.mkdir(parents=True, exist_ok=True)

    for variant in VARIANTS:
        ufo_path = REPO_ROOT / "source" / f"PlumMono-{variant}.ufo"
        run_fontmake(ufo_path)

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
             "Build the ttf files first with 'python build.py ttf'.")


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


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(
	        description="Python build pipeline for the Plum Mono typeface "
                    "(port of build-ttf.sh / build-woff.sh / build-woff2.sh).")
    parser.add_argument("target", nargs="?", default="all",
                        choices=["ttf", "woff", "woff2", "all"],
                        help="build target (default: all = ttf + woff + woff2)")
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
    elif args.target == "all":
        build_ttf()
        build_woff()
        build_woff2()


if __name__ == "__main__":
    main()
