# Plum Mono

A monospaced typeface for source code, based on [Hack](https://github.com/source-foundry/Hack).

![Plum Mono Showcase](imgs/plummono_showcase.png)

[中文说明](README.zh-CN.md)

---

## About

Plum Mono is a derivative of the [Hack](https://github.com/source-foundry/Hack) typeface,
which itself builds upon [DejaVu Sans Mono](https://dejavu-fonts.github.io/) and
[Bitstream Vera Sans Mono](https://www.gnome.org/fonts/).

The project redesigns a selection of Hack's punctuation and symbol glyphs for a different
visual character, using DejaVu Sans Mono designs as a basis with custom adjustments.

---

## Modifications

### Replaced glyphs

Taken from DejaVu Sans Mono and **emboldened** (interpolated between the Regular and Bold
weights):

| Glyph | Unicode |
|---|---|
| `:` | U+003A |
| `;` | U+003B |
| `,` | U+002C |
| `.` | U+002E |
| `"` | U+0022 |
| `'` | U+0027 |
| `*` | U+002A |

### Other adjustments

- **Asterisk** `*` — vertically centered to align with `+`
- **Underscore** `_` — extended to full width so adjacent underscores connect (`__` → no gap)
- **Digit `1`** — top serif angle adjusted to a middle ground between Hack and DejaVu
- **Digit `0`** — slashed zero, with a consistent slash width across all four styles
- **Combining marks** — 67 marks (U+0300–036F) ported into Regular so it covers the same
  codepoints as Bold/Italic/BoldItalic, plus `mark`/`mkmk` GPOS positioning.
  Details: [COMBINING_MARKS.md](COMBINING_MARKS.md)

### Zero variants

The default `0` is slashed. A **dotted zero** ships as an alt glyph and is built into its own
family, so both can be installed side by side:

| Family | `0` | How |
|---|---|---|
| Plum Mono | slashed | default build |
| Plum Mono `Dotted` | dotted | `python build.py all --alt dotted --suffix Dotted` |

---

## Building

The following are build examples; for detailed build commands, please refer to `python build.py --help`.

```bash
conda activate develop
python build.py --install-deps                        # pip: fontmake, fonttools, zopfli, brotli
python build.py ttf                                   # base family   -> build/ttf/PlumMono/
python build.py all --alt dotted --suffix Dotted      # dotted family -> build/ttf/PlumMono-Dotted/
```

Requires Python 3 with `fontmake`, `fonttools`, `zopfli`, `brotli`.

`build_bolder.py` is the same pipeline with one addition: after fontmake compiles the sources,
the Regular and Italic outlines are lightly emboldened (FontForge `changeWeight`, `--amount`,
default `25`; disable with `--no-embolden`). This replaces the two lighter styles in place —
the family is still a 4-style Regular/Bold/Italic/Bold Italic. It additionally requires
FontForge's `ffpython`.

### Output layout

`PlumMono[-Suffix]` is the family name with the spaces removed.

```
gen/PlumMono[-Suffix]/          generated variant sources (do not edit, gitignored)
build/ttf/PlumMono[-Suffix]/    ttf files (unhinted)
build/web/PlumMono[-Suffix]/    woff + woff2
source/                         the single hand-maintained UFO source
```

The build never writes to `source/`; `gen/` is disposable and regenerated on every build.
Web fonts are converted from the built TTFs, so build `ttf` first.

### Alt glyphs

```
source/alt-glyphs/<glyph>-<label>/<weight>/<glyph>.glif
```

A drop-in replacement for `<glyph>` in that weight: the part before the first `-` is the glyph
being replaced, the part after is the variant label. The build overlays the selected folders
onto a copy of the master UFOs and renames the family.

```bash
python build.py all --alt none                        # base only          "Plum Mono"
python build.py all --alt dotted                      # one variant        "Plum Mono Custom"
python build.py all --alt dotted --suffix Dotted      # own suffix         "Plum Mono Dotted"
python build.py all --alt dotted,foo --suffix One,Two # several variants, suffixes in order
```

- `--alt` — a label, a comma-separated list, `all` (base + every variant, the default), or `none`
- `--suffix` — family-name suffix, matched to the selected variants in order; default `Custom`
- The unmodified master always keeps the bare name `Plum Mono`

---

## License

Plum Mono is licensed under the MIT License.

Plum Mono is a derivative of Hack, which is licensed under the MIT License and incorporates work from the DejaVu project and Bitstream Vera Sans Mono.

See LICENSE for the complete license texts, copyright notices, and attribution information.
