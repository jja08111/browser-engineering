import tkinter
from constant import HEIGHT, SCROLL_STEP, SCROLLBAR_PADDING, SCROLLBAR_WIDTH, WIDTH
from layout import HSTEP, VSTEP, DisplayList, Layout
from parser import HTMLParser, Nodes, Element, create_html_parser, print_tree
from url import URL

SCROLLBAR_BOX_WIDHT = SCROLLBAR_WIDTH + 2 * SCROLLBAR_PADDING

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
    self.root: Element = None
    self.display_list: DisplayList = []

  def _content_max_y(self):
    return self.display_list[-1].y if self.display_list.__len__() else 0

  def _scroll_internal(self, delta: float):
    self.scroll -= delta
    window_height = self._window_height()
    max_y = self._content_max_y()
    if max_y < window_height:
      return
    if self.scroll < 0:
      self.scroll = 0
    if self.scroll + window_height > max_y:
      self.scroll = max_y - window_height
    self.draw_content()
    self.draw_scrollbar()
  
  def _window_height(self):
    return self.canvas.winfo_height()

  def _window_width(self) -> int:
    return self.canvas.winfo_width()

  def _should_draw_scrollbar(self) -> bool:
    max_y = self._content_max_y()
    window_height = self._window_height()
    return window_height < max_y

  def _viewport_width(self) -> int:
    if self._should_draw_scrollbar():
      return self._window_width() - SCROLLBAR_BOX_WIDHT
    return self._window_width()

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
    if not self._should_draw_scrollbar():
      return
    max_y = self._content_max_y()
    window_height = self._window_height()
    window_width = self._window_width()
    scrollbar_height = window_height * (window_height / max_y)
    x = window_width - SCROLLBAR_WIDTH - SCROLLBAR_PADDING
    current_scroll_percentage = self.scroll / (max_y - window_height)
    y = (window_height - scrollbar_height - 2 * SCROLLBAR_PADDING) * current_scroll_percentage
    y += SCROLLBAR_PADDING
    self.canvas.create_rectangle(x, y, x + SCROLLBAR_WIDTH, y + scrollbar_height, fill="gray")

  def draw_content(self):
    self.canvas.delete("all")
    height = self._window_height()
    for x, y, text, font in self.display_list:
      if y > self.scroll + height or y + VSTEP < self.scroll:
        continue
      self.canvas.create_text(
        x,
        y - self.scroll,
        text=text,
        anchor=tkinter.NW,
        font=font,
      )

  def layout_and_draw(self):
    viewport_width = self._viewport_width()
    if viewport_width < 0:
      return
    layout = Layout(viewport_width=viewport_width)
    self.display_list = layout.layout(self.root)
    self.draw_content()
    self.draw_scrollbar()

  def load(self, url: URL):
    try:
      body = url.request()
      self.root = create_html_parser(body=body).parse()
      print_tree(self.root)
      self.layout_and_draw()
    except Exception as e:
      print(f"Error: {e}")

if __name__ == "__main__":
  import sys
  Browser().load(URL(sys.argv[1]))
  tkinter.mainloop()
