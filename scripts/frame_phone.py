"""Composite a 1170x2298 content capture with an iOS-style status bar (132) and home indicator (102)
into a true 1170x2532 iPhone screen. Strip colours are sampled from the capture's own top/bottom rows."""
import sys, pathlib
from PIL import Image, ImageDraw, ImageFont
import os
FONT = os.environ.get('ALBERT_SANS_TTF', 'AlbertSans_600SemiBold.ttf')  # the app repo's assets/fonts/AlbertSans_600SemiBold.ttf
def lum(c): return 0.2126*c[0]+0.7152*c[1]+0.0722*c[2]
def bar(color, top=True):
    h = 132 if top else 102
    im = Image.new('RGB', (1170, h), color); d = ImageDraw.Draw(im)
    fg = (27,42,36) if lum(color) > 140 else (238,232,220)
    if top:
        f = ImageFont.truetype(FONT, 50)
        d.text((150, 66), '9:41', font=f, fill=fg, anchor='mm')
        x = 880  # signal bars
        for i in range(4):
            hh = 14 + i*9; d.rounded_rectangle((x+i*20, 84-hh, x+i*20+12, 84), 3, fill=fg)
        # wifi: three arcs
        cx, cy = 1000, 86
        for r in (36, 24, 12):
            d.pieslice((cx-r, cy-r, cx+r, cy+r), 225, 315, fill=fg)
            if r > 12:
                rr = r-7; d.pieslice((cx-rr, cy-rr, cx+rr, cy+rr), 225, 315, fill=color)
        # battery
        d.rounded_rectangle((1040, 52, 1110, 84), 9, outline=fg, width=4)
        d.rounded_rectangle((1047, 59, 1103, 77), 5, fill=fg)
        d.rounded_rectangle((1114, 62, 1120, 74), 2, fill=fg)
    else:
        d.rounded_rectangle((585-210, 60, 585+210, 75), 8, fill=fg)
    return im
for p in sys.argv[2:]:
    src = Image.open(p).convert('RGB')
    if src.size != (1170, 2298): src = src.resize((1170, 2298))
    top = src.getpixel((585, 2)); bot = src.getpixel((585, 2295))
    out = Image.new('RGB', (1170, 2532)); out.paste(bar(top, True), (0, 0)); out.paste(src, (0, 132)); out.paste(bar(bot, False), (0, 2430))
    dest = pathlib.Path(sys.argv[1]) / pathlib.Path(p).name
    out.save(dest)
