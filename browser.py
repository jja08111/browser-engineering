import tkinter
from constant import HEIGHT, SCROLL_STEP, SCROLLBAR_PADDING, SCROLLBAR_WIDTH, WIDTH
from layout import VSTEP, layout
from lexer import lex
from url import URL

class Browser:
  def __init__(self):
    self.window = tkinter.Tk()
    self.canvas = tkinter.Canvas(
      self.window,
      width=WIDTH,
      height=HEIGHT,
    )
    self.canvas.pack(fill=tkinter.BOTH, expand=True)
    self.scroll = 0
    self.window.bind("<Up>", self.scrollup)
    self.window.bind("<Down>", self.scrolldown)
    self.window.bind("<MouseWheel>", self.on_mouse_wheel)
    self.window.bind("<Configure>", self.on_configure)

  def _content_max_y(self):
    return self.display_list[-1].y if self.display_list.__len__() else 0

  def _scroll_internal(self, delta: float):
    self.scroll -= delta
    max_y = self._content_max_y()
    if self.scroll < 0:
      self.scroll = 0
    if self.scroll + self._window_height() > max_y:
      self.scroll = max_y - self._window_height()
    self.draw_content()
    self.draw_scrollbar()
  
  def _window_height(self):
    return self.canvas.winfo_height()
  
  def _window_width(self):
    return self.canvas.winfo_width()

  def scrollup(self, _):
    self._scroll_internal(-SCROLL_STEP)

  def scrolldown(self, _): 
    self._scroll_internal(SCROLL_STEP)
  
  def on_mouse_wheel(self, e):
    if e.delta > 0:
      self._scroll_internal(e.delta)
    elif e.delta < 0:
      self._scroll_internal(e.delta)

  def on_configure(self, _):
    self.layout_and_draw()

  def draw_scrollbar(self):
    max_y = self._content_max_y()
    window_height = self._window_height()
    window_width = self._window_width()
    if window_height > max_y:
      return
    scrollbar_height = window_height * (window_height / max_y)
    x = window_width - SCROLLBAR_WIDTH - SCROLLBAR_PADDING
    current_scroll_percentage = self.scroll / (max_y - window_height)
    y = (window_height - scrollbar_height - 2 * SCROLLBAR_PADDING) * current_scroll_percentage
    y += SCROLLBAR_PADDING
    self.canvas.create_rectangle(x, y, x + SCROLLBAR_WIDTH, y + scrollbar_height, fill="gray")

  def draw_content(self):
    self.canvas.delete("all")
    height = self._window_height()
    for x, y, c in self.display_list:
      if y > self.scroll + height or y + VSTEP < self.scroll:
        continue
      self.canvas.create_text(x, y - self.scroll, text=c)

  def layout_and_draw(self):
    self.display_list = layout(self.text, self._window_width())
    self.draw_content()
    self.draw_scrollbar()

  def load(self, url: URL):
    body = url.request()
    self.text = lex(body)
    self.layout_and_draw()

if __name__ == "__main__":
  import sys
  Browser().load(URL(sys.argv[1]))
  tkinter.mainloop()
