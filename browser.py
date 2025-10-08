import tkinter
from constant import HEIGHT, SCROLL_STEP, WIDTH
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

  def _scroll_internal(self, delta: float):
    self.scroll -= delta
    if self.scroll < 0:
      self.scroll = 0
    self.draw()

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
    self.layout_and_display()

  def draw(self):
    self.canvas.delete("all")
    height = self.canvas.winfo_height()
    for x, y, c in self.display_list:
      if y > self.scroll + height or y + VSTEP < self.scroll:
        continue
      self.canvas.create_text(x, y - self.scroll, text=c)
  
  def layout_and_display(self):
    self.display_list = layout(self.text, self.canvas.winfo_width())
    self.draw()

  def load(self, url: URL):
    body = url.request()
    self.text = lex(body)
    self.layout_and_display()

if __name__ == "__main__":
  import sys
  Browser().load(URL(sys.argv[1]))
  tkinter.mainloop()
