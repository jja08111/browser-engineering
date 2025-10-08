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
    self.canvas.pack()
    self.scroll = 0
    self.window.bind("<Down>", self.scrolldown)

  def scrolldown(self, _): 
    self.scroll += SCROLL_STEP
    self.draw()

  def draw(self):
    self.canvas.delete("all")
    for x, y, c in self.display_list:
      if y > self.scroll + HEIGHT or y + VSTEP < self.scroll:
        continue
      self.canvas.create_text(x, y - self.scroll, text=c)
  
  def load(self, url: URL):
    body = url.request()
    text = lex(body)
    self.display_list = layout(text)
    self.draw()

if __name__ == "__main__":
  import sys
  Browser().load(URL(sys.argv[1]))
  tkinter.mainloop()
