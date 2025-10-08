
from constant import WIDTH

HSTEP, VSTEP = 13, 18
NEWLINE_STEP = 24

def layout(text: str):
  display_list = []
  cursor_x, cursor_y = HSTEP, VSTEP
  for c in text:
    display_list.append((cursor_x, cursor_y, c))
    cursor_x += HSTEP
    if cursor_x >= WIDTH - HSTEP:
      cursor_x = 0
      cursor_y += VSTEP
    elif c == "\n":
      cursor_x = 0
      cursor_y += NEWLINE_STEP
  
  return display_list