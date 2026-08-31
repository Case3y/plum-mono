
# Plum Mono

A monospaced typeface for source code, based on [Hack](https://github.com/source-foundry/Hack).

---

## About

Plum Mono is a derivative of the [Hack](https://github.com/source-foundry/Hack) typeface,
which itself builds upon [DejaVu Sans Mono](https://dejavu-fonts.github.io/) and
[Bitstream Vera Sans Mono](https://www.gnome.org/fonts/).

This project modifies a selection of Hack's punctuation and symbol glyphs to give them
a different visual character, drawing from DejaVu Sans Mono with custom adjustments.

---

## Modifications

### Replaced glyphs

The following glyphs were replaced with versions from DejaVu Sans Mono and **bolder**
(interpolated between the Regular and Bold weights):

| Glyph | Unicode |
|---|---|
| `:` | U+003A |
| `;` | U+003B |
| `,` | U+002C |
| `.` | U+002E |
| `"` | U+0022 |
| `'` | U+0027 |
| `*` | U+002A |

### Additional adjustments

- **Asterisk** `*` — vertically centered to align with `+`
- **Underscore** `_` — extended to full width so adjacent underscores connect (`__` → no gap)
- **Digit** `1` — top serif angle adjusted to a middle ground between Hack and DejaVu

---

## Building

```bash
python build.py --install-deps
python build.py ttf
```

Requires: Python 3, fontmake, fonttools, ttfautohint.

---

## License

MIT License. See [LICENSE](LICENSE).
