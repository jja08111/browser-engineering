from abc import abstractmethod
import tkinter.font as tkfont 
from typing import List
import character_set
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
  is_sup: bool

  def __init__(self, x: int, text: str, font: tkfont.Font,
               is_sup: bool = False):
    self.x = x
    self.text = text
    self.font = font
    self.is_sup = is_sup

  def __iter__(self):
    yield self.x
    yield self.text
    yield self.font

DisplayList = List[DisplayItem]
Line = List[LineItem]

class Layout:
  def __init__(self, tokens: Tokens, viewport_width: int):
    self.display_list: DisplayList = []
    self.cursor_x: int = HSTEP
    self.cursor_y: int = VSTEP
    self.weight: Weight = DEFAULT_WEIGHT
    self.style: Style = DEFAULT_STYLE
    self.viewport_width: int = viewport_width
    self.tokens: Tokens = tokens
    self.size: int = 12
    self.line: Line = []
    self.is_sup: bool = False
    self.is_abbr: bool = False
    self.abbr_buffer = ""
    self.is_pre: bool = False

  def handle_word(self, word: str, trailing_character: str = character_set.SPACE):
    font = get_font(self.size, self.weight, self.style, family="Courier New" if self.is_pre else None)
    word_and_space_width = font.measure(word + trailing_character)
    if self.cursor_x + word_and_space_width >= self.viewport_width:
      parts = word.split(character_set.SOFT_HYPHEN)
      if parts.__len__() > 1 and not self.is_sup:
        part_index = 0
        while True:
          candidate = ""
          while part_index < len(parts):
            if (self.cursor_x + font.measure(candidate + parts[part_index] + character_set.HYPHEN)
                    >= self.viewport_width):
              break
            candidate += parts[part_index]
            part_index += 1
          if not candidate and self.cursor_x == HSTEP:
            self.line.append(LineItem(x=self.cursor_x, text=word, font=font))
            self.flush()
            return

          if part_index < len(parts):
            if candidate:
              item = LineItem(x=self.cursor_x, text=candidate + character_set.HYPHEN,
                              font=font)
              self.line.append(item)
            self.flush()
          else:
            self.line.append(LineItem(x=self.cursor_x, text=candidate, font=font))
            self.cursor_x += font.measure(candidate + trailing_character)
            return
      else:
        self.flush()
    item = LineItem(x=self.cursor_x, text=word, font=font, is_sup=self.is_sup)
    self.line.append(item)
    self.cursor_x += word_and_space_width

  def flush(self):
    if not self.line:
      return
    metrics = [font.metrics() for _, _, font in self.line]
    max_ascent = max([metric["ascent"] for metric in metrics])
    # TODO: This is a simple implementation. We need to consider variant fonts.
    baseline = self.cursor_y + LEADING_RATIO * max_ascent
    for item in self.line:
      (x, word, font) = item
      ascent = font.metrics("ascent")
      y = baseline - ascent if not item.is_sup else self.cursor_y
      self.display_list.append(DisplayItem(x=x, y=y, text=word, font=font))
    max_descent = max([metric["descent"] for metric in metrics])
    self.cursor_y = baseline + 1.25 * max_descent
    self.cursor_x = HSTEP
    self.line = []

  def handle_abbr(self):
    text = (self.abbr_buffer or "").strip()
    original_size = self.size
    original_weight = self.weight
    word_buffer = ""
    is_prev_lower = None
    for ch in text:
      if ch.isspace():
        self.handle_word(word_buffer)
        word_buffer = ""
      elif ch.isupper() or ch.isdigit():
        if is_prev_lower is None or is_prev_lower:
          self.handle_word(word_buffer.upper(), trailing_character="")
          word_buffer = ""
          self.size = original_size
          self.weight = original_weight
        is_prev_lower = False
        word_buffer += ch
      elif ch.islower():
        if is_prev_lower is None or not is_prev_lower:
          self.handle_word(word_buffer, trailing_character="")
          word_buffer = ""
          self.size -= 2
          self.weight = "bold"
        is_prev_lower = True
        word_buffer += ch

    if word_buffer:
      self.handle_word(word_buffer.upper() if is_prev_lower else word_buffer)

    # abbr 상태 해제
    self.is_abbr = False
    self.abbr_buffer = ""
    self.size = original_size
    self.weight = original_weight

  def layout(self) -> List[DisplayItem]:
    for token in self.tokens:
      if isinstance(token, Text):
        if self.is_abbr:
          self.abbr_buffer += token.text
        elif self.is_pre:
          splitted = token.text.split("\n")
          for index, line in enumerate(splitted):
            self.handle_word(word=line)
            if index + 1 < len(splitted):
              self.flush()
        else:
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
        start_x = (self.viewport_width - line_width) / 2
        for item in self.line:
          item.x += start_x
        self.flush()
      elif token.tag == "sup":
        self.size = int(self.size / 2)
        self.is_sup = True
      elif token.tag == "/sup":
        self.size *= 2
        self.is_sup = False
      elif token.tag == "abbr":
        self.is_abbr = True
        self.abbr_buffer = ""
      elif token.tag == "/abbr":
        self.handle_abbr()
      elif token.tag == "pre":
        self.is_pre = True
      elif token.tag == "/pre":
        self.is_pre = False
        self.flush()

    self.flush()
    return self.display_list