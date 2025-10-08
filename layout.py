from typing import List

HSTEP, VSTEP = 13, 18
NEWLINE_STEP = 24

class DisplayList:
  x: int
  y: int
  c: str

def layout(text: str, width: int) -> List[DisplayList]:
  display_list: List[DisplayList] = []
  cursor_x, cursor_y = HSTEP, VSTEP
  for c in text:
    display_list.append((cursor_x, cursor_y, c))
    cursor_x += HSTEP
    if cursor_x >= width - HSTEP:
      cursor_x = HSTEP
      cursor_y += VSTEP
    elif c == "\n":
      cursor_x = HSTEP
      cursor_y += NEWLINE_STEP
  
  return display_list