from typing import List

HSTEP, VSTEP = 13, 18
NEWLINE_STEP = 24

class DisplayItem:
  x: int
  y: int
  c: str

  def __init__(self, x: int, y: int, c: str):
    self.x = x
    self.y = y
    self.c = c
  
  def __iter__(self):
    yield self.x
    yield self.y
    yield self.c

# TODO: Consider content view width because of scrollbar?
def layout(text: str, width: int) -> List[DisplayItem]:
  display_list: List[DisplayItem] = []
  cursor_x, cursor_y = HSTEP, VSTEP
  for c in text:
    display_item = DisplayItem(x=cursor_x, y=cursor_y, c=c)
    display_list.append(display_item)
    cursor_x += HSTEP
    if cursor_x >= width - HSTEP:
      cursor_x = HSTEP
      cursor_y += VSTEP
    elif c == "\n":
      cursor_x = HSTEP
      cursor_y += NEWLINE_STEP
  
  return display_list