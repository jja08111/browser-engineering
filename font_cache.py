from tkinter import Label
from tkinter.font import Font
from typing import Optional
from font_weight import Weight
from style import Style

FONTS = {}

def get_font(size: int, weight: Weight, style: Style, family: Optional[str] = None) -> Font:
  key = (size, weight, style, family)
  if key not in FONTS:
    font = Font(
      size=size,
      weight=weight,
      slant=style,
      family=family,
    )
    label = Label(font=font)
    FONTS[key] = (font, label)
  return FONTS[key][0]