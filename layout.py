import tkinter.font as tkfont 
from typing import List
from constant import SCROLLBAR_PADDING, SCROLLBAR_WIDTH
from font_cache import get_font
from font_weight import DEFAULT_WEIGHT, Weight
from lexer import Text, Tokens
from style import DEFAULT_STYLE, Style

HSTEP, VSTEP = 13, 18
NEWLINE_STEP = 24
LEADING_RATIO = 1.25

class DisplayItem:
  x: int
  y: int
  text: str
  font: tkfont.Font

  def __init__(self, x: int, y: int, text: str, font: tkfont.Font):
    self.x = x
    self.y = y
    self.text = text
    self.font = font
  
  def __iter__(self):
    yield self.x
    yield self.y
    yield self.text
    yield self.font

class LineItem:
  x: int
  text: str
  font: tkfont.Font

  def __init__(self, x: int, text: str, font: tkfont.Font):
    self.x = x
    self.text = text
    self.font = font

  def __iter__(self):
    yield self.x
    yield self.text
    yield self.font

DisplayList = List[DisplayItem]
Line = List[LineItem]

SCROLLBAR_BOX_WIDHT = SCROLLBAR_WIDTH + 2 * SCROLLBAR_PADDING

class Layout:
  def __init__(self, tokens: Tokens, window_width: int):
    self.display_list: DisplayList = []
    self.cursor_x: int = HSTEP
    self.cursor_y: int = VSTEP
    self.weight: Weight = DEFAULT_WEIGHT
    self.style: Style = DEFAULT_STYLE
    self.window_width: int = window_width
    self.tokens: Tokens = tokens
    self.size: int = 12
    self.line: Line = []
  
  def _content_width(self) -> int:
    return self.window_width - SCROLLBAR_BOX_WIDHT - 2 * HSTEP

  def handle_word(self, word: str):
    font = get_font(self.size, self.weight, self.style)
    word_width = font.measure(word)
    self.line.append(LineItem(x=self.cursor_x, text=word, font=font))
    self.cursor_x += word_width + font.measure(" ")
    if self.cursor_x + word_width >= self._content_width():
      self.cursor_y += font.metrics("linespace") * 1.25
      self.cursor_x = HSTEP
      self.flush()

  def flush(self):
    if not self.line:
      return
    metrics = [font.metrics() for _, _, font in self.line]
    max_ascent = max([metric["ascent"] for metric in metrics])
    # TODO: This is a simple implementation. We need to consider variant fonts.
    baseline = self.cursor_y + LEADING_RATIO * max_ascent
    for x, word, font in self.line:
      y = baseline - font.metrics("ascent")
      self.display_list.append(DisplayItem(x=x, y=y, text=word, font=font))
    max_descent = max([metric["descent"] for metric in metrics])
    self.cursor_y = baseline + 1.25 * max_descent
    self.cursor_x = HSTEP
    self.line = []

  def layout(self) -> List[DisplayItem]:
    for token in self.tokens:
      if isinstance(token, Text):
        for word in token.text.split():
          self.handle_word(word=word)
      # TODO: Fix the |view-source| feature
      elif token.tag == "i":
        self.style = "italic"
      elif token.tag == "/i":
        self.style = DEFAULT_STYLE
      elif token.tag == "b":
        self.weight = "bold"
      elif token.tag == "/b":
        self.weight = DEFAULT_WEIGHT 
      elif token.tag == "small":
        self.size -= 2
      elif token.tag == "/small":
        self.size += 2
      elif token.tag == "big":
        self.size += 4
      elif token.tag == "/big":
        self.size -= 4
      elif token.tag == "br":
        self.flush()
      elif token.tag == "/p":
        self.flush()
        self.cursor_y += VSTEP
      elif token.tag == "/h1":
        line_len = self.line.__len__()
        line_width = (self.cursor_x - self.line[0].x) if line_len else 0
        start_x = (self._content_width() - line_width) / 2
        for item in self.line:
          item.x += start_x
        self.flush()

    self.flush()
    return self.display_list