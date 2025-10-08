
from constant import WIDTH

HSTEP, VSTEP = 13, 18

def layout(text: str):
  display_list = []
  cursor_x, cursor_y = HSTEP, VSTEP
  for c in text:
    display_list.append((cursor_x, cursor_y, c))
    cursor_x += HSTEP
    if cursor_x >= WIDTH - HSTEP:
      cursor_x = 0
      cursor_y += VSTEP
  
  return display_list