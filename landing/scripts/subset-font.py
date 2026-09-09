"""Build the English/Latin subset of the bundled Inter variable font.

Requires fonttools[woff] at build time only; preserves the font's variable axes.
"""
from pathlib import Path
from fontTools import subset
from fontTools.pens.svgPathPen import SVGPathPen

root = Path(__file__).resolve().parents[1]
source = root.parent / 'photobooth-frontend/src/css/fonts/Inter-4.0/web/InterVariable.woff2'
destination = root / 'assets/fonts/inter-latin.woff2'
destination.parent.mkdir(parents=True, exist_ok=True)
options = subset.Options()
options.flavor = 'woff2'
options.layout_features = ['kern', 'liga', 'calt', 'case']
font = subset.load_font(str(source), options)
subsetter = subset.Subsetter(options=options)
subsetter.populate(unicodes=[*range(0x20, 0x7F), 0xA0, 0xD7, 0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2026, 0x2191, 0x20B1])
subsetter.subset(font)
subset.save_font(font, str(destination), options)
print(f'{destination.name}: {destination.stat().st_size} bytes')

# Outline the social card's Inter lettering so SVG rendering never substitutes a system font.
units = font['head'].unitsPerEm
cmap = font.getBestCmap()
parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630"><rect width="1200" height="630" fill="#F7F3EB"/>']
for text, x, y, size, weight in [
    ('Motif Moments', 60, 110, 30, 650),
    ('Make it a motif.', 60, 260, 62, 600),
    ('Keep the memory.', 60, 335, 62, 600),
    ('Your people. Your poses. Your little keepsake.', 60, 500, 22, 400),
]:
    glyphs = font.getGlyphSet(location={'wght': weight})
    scale = size / units
    for char in text:
        glyph = glyphs[cmap[ord(char)]]
        pen = SVGPathPen(glyphs)
        glyph.draw(pen)
        parts.append(f'<path fill="#171717" transform="translate({x},{y}) scale({scale},-{scale})" d="{pen.getCommands()}"/>')
        x += glyph.width * scale - size * 0.02
parts.append('</svg>')
(root / 'assets/social-type.svg').write_text(''.join(parts), encoding='utf-8')
