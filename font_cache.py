import tkinter
from font_weight import Weight
from style import Style

FONTS = {}

def get_font(size: int, weight: Weight, style: Style):
  key = (size, weight, style)
  if key not in FONTS:
    font = tkinter.font.Font(size=size, weight=weight,
        slant=style)
    label = tkinter.Label(font=font)
    FONTS[key] = (font, label)
  return FONTS[key][0]