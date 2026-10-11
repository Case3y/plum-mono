# PlumMono-Regular 组合标记移植清单

## 概览

- 移植字形总数：**67**（61 个基础标记 + 6 个 `.case` 大写变体）
- Regular 现映射 **66 个组合码位**，与 Bold/Italic/BoldItalic 完全一致
- 另有 5 个原先就存在的命名标记（见附录），合计覆盖 U+0300–033F 全部码位 + U+0358/U+0361

| 推导组 | 数量 | 方法 |
|---|---|---|
| A | 8 | Regular spacing 修饰符轮廓左移 −1233（字重/风格 100% 原生）|
| A2 | 4 | Regular 大写预组合字形的高区部件（y>1550）左移 −1233 |
| B | 55 | Italic 同名字形反剪切 tan 11°（Regular 字重）+ 中心对齐 Bold 网格 |

## 67 个移植标记

> 「测试」列 = `x` + 该标记，可直接粘贴到编辑器中用 Plum Mono Regular 查看定位效果。
> 「y 范围」为字体单位（2048 UPM）：正值在基线上方，负值在基线下方。

| # | 字形 | 码位 | 字符 | Unicode 名称 | 测试 | 组 | 来源 | y 范围 |
|---|---|---|---|---|---|---|---|---|
| 1 | `uni0302` | U+0302 | ̂ | COMBINING CIRCUMFLEX ACCENT | `x̂` | A | circumflex (U+02C6) | 1262…1638 |
| 2 | `uni0304` | U+0304 | ̄ | COMBINING MACRON | `x̄` | A | macron (U+00AF) | 1378…1526 |
| 3 | `uni0304.case` | — | — | （无码位，GSUB case 备用字形） | `—` | A2 | Amacron 部件 | 1652…1800 |
| 4 | `uni0305` | U+0305 | ̅ | COMBINING OVERLINE | `x̅` | B | Italic 反剪切 + 对齐 Bold | 1467…1547 |
| 5 | `uni0306` | U+0306 | ̆ | COMBINING BREVE | `x̆` | A | breve (U+02D8) | 1321…1608 |
| 6 | `uni0306.case` | — | — | （无码位，GSUB case 备用字形） | `—` | A2 | Abreve 部件 | 1589…1831 |
| 7 | `uni0307` | U+0307 | ̇ | COMBINING DOT ABOVE | `ẋ` | A | dotaccent (U+02D9) | 1348…1552 |
| 8 | `uni0307.case` | — | — | （无码位，GSUB case 备用字形） | `—` | A2 | Cdotaccent 部件 | 1647…1852 |
| 9 | `uni0308` | U+0308 | ̈ | COMBINING DIAERESIS | `ẍ` | A | dieresis (U+00A8) | 1350…1552 |
| 10 | `uni030A` | U+030A | ̊ | COMBINING RING ABOVE | `x̊` | A | ring (U+02DA) | 1249…1798 |
| 11 | `uni030B` | U+030B | ̋ | COMBINING DOUBLE ACUTE ACCENT | `x̋` | A | hungarumlaut (U+02DD) | 1262…1638 |
| 12 | `uni030B.case` | — | — | （无码位，GSUB case 备用字形） | `—` | A2 | Ohungarumlaut 部件 | 1595…1859 |
| 13 | `uni030C` | U+030C | ̌ | COMBINING CARON | `x̌` | A | caron (U+02C7) | 1262…1638 |
| 14 | `uni030D` | U+030D | ̍ | COMBINING VERTICAL LINE ABOVE | `x̍` | B | Italic 反剪切 + 对齐 Bold | 1262…1706 |
| 15 | `uni030E` | U+030E | ̎ | COMBINING DOUBLE VERTICAL LINE ABOVE | `x̎` | B | Italic 反剪切 + 对齐 Bold | 1262…1706 |
| 16 | `uni030F` | U+030F | ̏ | COMBINING DOUBLE GRAVE ACCENT | `x̏` | B | Italic 反剪切 + 对齐 Bold | 1262…1638 |
| 17 | `uni030F.case` | — | — | （无码位，GSUB case 备用字形） | `—` | B | Italic 反剪切 + 对齐 Bold | 1635…1899 |
| 18 | `uni0310` | U+0310 | ̐ | COMBINING CANDRABINDU | `x̐` | B | Italic 反剪切 + 对齐 Bold | 1525…1812 |
| 19 | `uni0311` | U+0311 | ̑ | COMBINING INVERTED BREVE | `x̑` | B | Italic 反剪切 + 对齐 Bold | 1321…1608 |
| 20 | `uni0311.case` | — | — | （无码位，GSUB case 备用字形） | `—` | B | Italic 反剪切 + 对齐 Bold | 1659…1901 |
| 21 | `uni0312` | U+0312 | ̒ | COMBINING TURNED COMMA ABOVE | `x̒` | B | Italic 反剪切 + 对齐 Bold | 967…1312 |
| 22 | `uni0313` | U+0313 | ̓ | COMBINING COMMA ABOVE | `x̓` | B | Italic 反剪切 + 对齐 Bold | 1218…1729 |
| 23 | `uni0314` | U+0314 | ̔ | COMBINING REVERSED COMMA ABOVE | `x̔` | B | Italic 反剪切 + 对齐 Bold | 1218…1729 |
| 24 | `uni0315` | U+0315 | ̕ | COMBINING COMMA ABOVE RIGHT | `x̕` | B | Italic 反剪切 + 对齐 Bold | 1262…1638 |
| 25 | `uni0316` | U+0316 | ̖ | COMBINING GRAVE ACCENT BELOW | `x̖` | B | Italic 反剪切 + 对齐 Bold | -584…-208 |
| 26 | `uni0317` | U+0317 | ̗ | COMBINING ACUTE ACCENT BELOW | `x̗` | B | Italic 反剪切 + 对齐 Bold | -584…-208 |
| 27 | `uni0318` | U+0318 | ̘ | COMBINING LEFT TACK BELOW | `x̘` | B | Italic 反剪切 + 对齐 Bold | -767…-277 |
| 28 | `uni0319` | U+0319 | ̙ | COMBINING RIGHT TACK BELOW | `x̙` | B | Italic 反剪切 + 对齐 Bold | -767…-277 |
| 29 | `uni031A` | U+031A | ̚ | COMBINING LEFT ANGLE ABOVE | `x̚` | B | Italic 反剪切 + 对齐 Bold | 1414…1904 |
| 30 | `uni031B` | U+031B | ̛ | COMBINING HORN | `x̛` | B | Italic 反剪切 + 对齐 Bold | 764…1137 |
| 31 | `uni031C` | U+031C | ̜ | COMBINING LEFT HALF RING BELOW | `x̜` | B | Italic 反剪切 + 对齐 Bold | -502…-63 |
| 32 | `uni031D` | U+031D | ̝ | COMBINING UP TACK BELOW | `x̝` | B | Italic 反剪切 + 对齐 Bold | -590…-277 |
| 33 | `uni031E` | U+031E | ̞ | COMBINING DOWN TACK BELOW | `x̞` | B | Italic 反剪切 + 对齐 Bold | -590…-277 |
| 34 | `uni031F` | U+031F | ̟ | COMBINING PLUS SIGN BELOW | `x̟` | B | Italic 反剪切 + 对齐 Bold | -767…-277 |
| 35 | `uni0320` | U+0320 | ̠ | COMBINING MINUS SIGN BELOW | `x̠` | B | Italic 反剪切 + 对齐 Bold | -413…-277 |
| 36 | `uni0321` | U+0321 | ̡ | COMBINING PALATALIZED HOOK BELOW | `x̡` | B | Italic 反剪切 + 对齐 Bold | -426…128 |
| 37 | `uni0322` | U+0322 | ̢ | COMBINING RETROFLEX HOOK BELOW | `x̢` | B | Italic 反剪切 + 对齐 Bold | -426…128 |
| 38 | `uni0324` | U+0324 | ̤ | COMBINING DIAERESIS BELOW | `x̤` | B | Italic 反剪切 + 对齐 Bold | -412…-210 |
| 39 | `uni0325` | U+0325 | ̥ | COMBINING RING BELOW | `x̥` | B | Italic 反剪切 + 对齐 Bold | -502…-63 |
| 40 | `uni0326` | U+0326 | ̦ | COMBINING COMMA BELOW | `x̦` | B | Italic 反剪切 + 对齐 Bold | -542…-197 |
| 41 | `uni0327` | U+0327 | ̧ | COMBINING CEDILLA | `x̧` | B | Italic 反剪切 + 对齐 Bold | -395…0 |
| 42 | `uni0328` | U+0328 | ̨ | COMBINING OGONEK | `x̨` | B | Italic 反剪切 + 对齐 Bold | -395…0 |
| 43 | `uni0329` | U+0329 | ̩ | COMBINING VERTICAL LINE BELOW | `x̩` | B | Italic 反剪切 + 对齐 Bold | -653…-209 |
| 44 | `uni032A` | U+032A | ̪ | COMBINING BRIDGE BELOW | `x̪` | B | Italic 反剪切 + 对齐 Bold | -539…-209 |
| 45 | `uni032B` | U+032B | ̫ | COMBINING INVERTED DOUBLE ARCH BELOW | `x̫` | B | Italic 反剪切 + 对齐 Bold | -455…-168 |
| 46 | `uni032C` | U+032C | ̬ | COMBINING CARON BELOW | `x̬` | B | Italic 反剪切 + 对齐 Bold | -485…-109 |
| 47 | `uni032D` | U+032D | ̭ | COMBINING CIRCUMFLEX ACCENT BELOW | `x̭` | B | Italic 反剪切 + 对齐 Bold | -485…-109 |
| 48 | `uni032E` | U+032E | ̮ | COMBINING BREVE BELOW | `x̮` | B | Italic 反剪切 + 对齐 Bold | -487…-200 |
| 49 | `uni032F` | U+032F | ̯ | COMBINING INVERTED BREVE BELOW | `x̯` | B | Italic 反剪切 + 对齐 Bold | -485…-198 |
| 50 | `uni0330` | U+0330 | ̰ | COMBINING TILDE BELOW | `x̰` | B | Italic 反剪切 + 对齐 Bold | -487…-203 |
| 51 | `uni0331` | U+0331 | ̱ | COMBINING MACRON BELOW | `x̱` | B | Italic 反剪切 + 对齐 Bold | -357…-209 |
| 52 | `uni0332` | U+0332 | ̲ | COMBINING LOW LINE | `x̲` | B | Italic 反剪切 + 对齐 Bold | -483…-403 |
| 53 | `uni0333` | U+0333 | ̳ | COMBINING DOUBLE LOW LINE | `x̳` | B | Italic 反剪切 + 对齐 Bold | -483…-163 |
| 54 | `uni0334` | U+0334 | ̴ | COMBINING TILDE OVERLAY | `x̴` | B | Italic 反剪切 + 对齐 Bold | 492…780 |
| 55 | `uni0335` | U+0335 | ̵ | COMBINING SHORT STROKE OVERLAY | `x̵` | B | Italic 反剪切 + 对齐 Bold | 452…616 |
| 56 | `uni0336` | U+0336 | ̶ | COMBINING LONG STROKE OVERLAY | `x̶` | B | Italic 反剪切 + 对齐 Bold | 452…616 |
| 57 | `uni0337` | U+0337 | ̷ | COMBINING SHORT SOLIDUS OVERLAY | `x̷` | B | Italic 反剪切 + 对齐 Bold | -96…1212 |
| 58 | `uni0338` | U+0338 | ̸ | COMBINING LONG SOLIDUS OVERLAY | `x̸` | B | Italic 反剪切 + 对齐 Bold | -70…1559 |
| 59 | `uni0339` | U+0339 | ̹ | COMBINING RIGHT HALF RING BELOW | `x̹` | B | Italic 反剪切 + 对齐 Bold | -502…-63 |
| 60 | `uni033A` | U+033A | ̺ | COMBINING INVERTED BRIDGE BELOW | `x̺` | B | Italic 反剪切 + 对齐 Bold | -384…-54 |
| 61 | `uni033B` | U+033B | ̻ | COMBINING SQUARE BELOW | `x̻` | B | Italic 反剪切 + 对齐 Bold | -759…-209 |
| 62 | `uni033C` | U+033C | ̼ | COMBINING SEAGULL BELOW | `x̼` | B | Italic 反剪切 + 对齐 Bold | -455…-168 |
| 63 | `uni033D` | U+033D | ̽ | COMBINING X ABOVE | `x̽` | B | Italic 反剪切 + 对齐 Bold | 1228…1671 |
| 64 | `uni033E` | U+033E | ̾ | COMBINING VERTICAL TILDE | `x̾` | B | Italic 反剪切 + 对齐 Bold | 1218…1746 |
| 65 | `uni033F` | U+033F | ̿ | COMBINING DOUBLE OVERLINE | `x̿` | B | Italic 反剪切 + 对齐 Bold | 1227…1307 |
| 66 | `uni0358` | U+0358 | ͘ | COMBINING DOT ABOVE RIGHT | `x͘` | B | Italic 反剪切 + 对齐 Bold | 1348…1552 |
| 67 | `uni0361` | U+0361 | ͡ | COMBINING DOUBLE INVERTED BREVE | `x͡` | B | Italic 反剪切 + 对齐 Bold | 1520…1847 |

## 附录：原先已存在的 5 个命名标记

| 字形 | 码位 | 字符 | Unicode 名称 | 测试 |
|---|---|---|---|---|
| `gravecomb` | U+0300 | ̀ | COMBINING GRAVE ACCENT | `x̀` |
| `acutecomb` | U+0301 | ́ | COMBINING ACUTE ACCENT | `x́` |
| `tildecomb` | U+0303 | ̃ | COMBINING TILDE | `x̃` |
| `hookabovecomb` | U+0309 | ̉ | COMBINING HOOK ABOVE | `x̉` |
| `dotbelowcomb` | U+0323 | ̣ | COMBINING DOT BELOW | `x̣` |

## 快速验证

```
x x̄   X X̄   a ā   x x̱   p p̂   e ë   o o̧   x x̅   l l̄   g g̣
```

- 上方标记应悬停在基字符顶部之上（大写基字符时更高）
- 下方标记（x̱ 的下横线、o̧ 的 cedilla）应挂在基线之下
- **GPOS 定位（第 2 步）已生效**：`l̄` 的横线应清过 l 的上伸部分，`g̣` 的下点应降到 g 的降部之下，`X̄` 的横线应在大写高度之上

