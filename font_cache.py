import tkinter
from typing import Optional
from font_weight import Weight
from style import Style

FONTS = {}

def get_font(size: int, weight: Weight, style: Style, family: Optional[str] = None):
  key = (size, weight, style, family)
  if key not in FONTS:
    font = tkinter.font.Font(
      size=size,
      weight=weight,
      slant=style,
      family=family,
    )
    label = tkinter.Label(font=font)
    FONTS[key] = (font, label)
  return FONTS[key][0]