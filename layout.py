from abc import abstractmethod
from tkinter import Canvas
import tkinter.font as tkfont 
from typing import List
import character_set
from font_cache import get_font
from font_weight import DEFAULT_WEIGHT, Weight
from parser import Element, Text, Node
from style import DEFAULT_STYLE, Style
from enum import Enum

HSTEP, VSTEP = 13, 18
NEWLINE_STEP = 24
LEADING_RATIO = 1.25

BLOCK_ELEMENTS = [
  "html", "body", "article", "section", "nav", "aside",
  "h1", "h2", "h3", "h4", "h5", "h6", "hgroup", "header",
  "footer", "address", "p", "hr", "pre", "blockquote",
  "ol", "ul", "menu", "li", "dl", "dt", "dd", "figure",
  "figcaption", "main", "div", "table", "form", "fieldset",
  "legend", "details", "summary"
]

class LayoutMode(Enum):
    INLINE = 1
    BLOCK = 2

class DrawText:
  def __init__(self, x1: int, y1: int, text: str, font: tkfont.Font) -> None:
    self.top = y1
    self.left = x1
    self.text = text
    self.font = font
    self.bottom = y1 + font.metrics("linespace")

  def execute(self, scroll: int, canvas: Canvas):
    canvas.create_text(
      self.left, self.top - scroll,
      text=self.text,
      font=self.font,
      anchor="nw"
    )

class DrawRect:
  def __init__(self, x1: int, y1: int, x2: int, y2: int, color: str) -> None:
    self.top = y1
    self.left = x1
    self.bottom = y2
    self.right = x2
    self.color = color

  def execute(self, scroll: int, canvas: Canvas):
    canvas.create_rectangle(
      self.left, self.top - scroll,
      self.right, self.bottom - scroll,
      width=0,
      fill=self.color,
    )

Command = DrawText | DrawRect
Commands = list[Command]

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
  
  def __repr__(self) -> str:
    return f"[x: {self.x}, y: {self.y}, text: {self.text}, font: {self.font}]"

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

class BlockLayout:
  def __init__(self, node: Node, parent, previous):
    assert(isinstance(parent, (BlockLayout, DocumentLayout)))
    assert(isinstance(previous, BlockLayout) or previous is None)
    self.display_list: DisplayList = []
    self.node: Node = node
    self.parent: BlockLayout | DocumentLayout = parent
    self.previous: BlockLayout | None = previous
    self.children: list[BlockLayout] = []
    self.x: int | None = None
    self.y: int | None = None
    self.width: int | None = None
    self.height: int | None = None

  def handle_word(self, word: str, trailing_character: str = character_set.SPACE):
    font = get_font(self.size, self.weight, self.style, family="Courier New" if self.is_pre else None)
    word_and_space_width = font.measure(word + trailing_character)
    if self.cursor_x + word_and_space_width >= self.width:
      parts = word.split(character_set.SOFT_HYPHEN)
      if parts.__len__() > 1 and not self.is_sup:
        part_index = 0
        while True:
          candidate = ""
          while part_index < len(parts):
            if (self.cursor_x + font.measure(candidate + parts[part_index] + character_set.HYPHEN)
                    >= self.width):
              break
            candidate += parts[part_index]
            part_index += 1
          # TODO: We should check here. The `0` is right to compare?
          if not candidate and self.cursor_x == 0:
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
      (rel_x, word, font) = item
      x = self.x + rel_x
      y = self.y + (baseline - font.metrics("ascent") if not item.is_sup else self.cursor_y)
      self.display_list.append(DisplayItem(x=x, y=y, text=word, font=font))
    max_descent = max([metric["descent"] for metric in metrics])
    self.cursor_y = baseline + 1.25 * max_descent
    self.cursor_x = 0
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
  
  def handle_open_tag(self, tag: str):
    if tag == "i":
        self.style = "italic"
    elif tag == "b":
      self.weight = "bold"
    elif tag == "small":
      self.size -= 2
    elif tag == "big":
      self.size += 4
    elif tag == "br":
      self.flush()
    elif tag == "sup":
      self.size = int(self.size / 2)
      self.is_sup = True
    elif tag == "abbr":
      self.is_abbr = True
      self.abbr_buffer = ""
    elif tag == "pre":
      self.is_pre = True
  
  def handle_close_tag(self, tag: str):
    if tag == "i":
        self.style = DEFAULT_STYLE
    elif tag == "b":
      self.weight = DEFAULT_WEIGHT 
    elif tag == "small":
      self.size += 2
    elif tag == "big":
      self.size -= 4
    elif tag == "p":
      self.flush()
      self.cursor_y += VSTEP
    elif tag == "li":
      self.flush()
    elif tag == "h1":
      line_len = self.line.__len__()
      line_width = (self.cursor_x - self.line[0].x) if line_len else 0
      start_x = (self.width - line_width) / 2
      for item in self.line:
        item.x += start_x
      self.flush()
    elif tag == "sup":
      self.size *= 2
      self.is_sup = False
    elif tag == "abbr":
      self.handle_abbr()
    elif tag == "pre":
      self.is_pre = False
      # TODO: Is it right to flush in here?
      self.flush()

  def recurse(self, root: Node):
    if isinstance(root, Text):
      if self.is_abbr:
        self.abbr_buffer += root.text
      elif self.is_pre:
        splitted = root.text.split("\n")
        for index, line in enumerate(splitted):
          self.handle_word(word=line)
          if index + 1 < len(splitted):
            self.flush()
      else:
        for word in root.text.split():
          self.handle_word(word=word)
    else:
      self.handle_open_tag(root.tag)
      for child in root.children:
        self.recurse(child)
      self.handle_close_tag(root.tag)

  def layout_mode(self) -> LayoutMode:
    if isinstance(self.node, Text):
      return LayoutMode.INLINE
    elif any([isinstance(child, Element) and \
              child.tag in BLOCK_ELEMENTS \
              for child in self.node.children]):
      return LayoutMode.BLOCK
    elif self.node.children:
      return LayoutMode.INLINE
    else:
      return LayoutMode.BLOCK

  def layout(self):
    self.x = self.parent.x
    self.width = self.parent.width
    if self.previous:
      self.y = self.previous.y + self.previous.height
    else:
      self.y = self.parent.y
    mode = self.layout_mode()
    if mode == LayoutMode.BLOCK:
      previous: BlockLayout | None = None
      for child in self.node.children:
        next = BlockLayout(node=child, parent=self, previous=previous)
        self.children.append(next)
        previous = next
    else:
      self.cursor_x: int = 0
      self.cursor_y: int = 0
      self.weight: Weight = DEFAULT_WEIGHT
      self.style: Style = DEFAULT_STYLE
      self.size: int = 12
      self.is_sup: bool = False
      self.is_abbr: bool = False
      self.abbr_buffer = ""
      self.is_pre: bool = False

      self.line: Line = []
      self.recurse(root=self.node)
      self.flush()

      self.height = self.cursor_y
    
    for child in self.children:
      child.layout()
    
    if mode == LayoutMode.BLOCK:
      self.height = sum([
          child.height for child in self.children])
  
  def paint(self) -> Commands:
    commands: Commands = []
    if isinstance(self.node, Element) and self.node.tag == "nav" and \
       "class" in self.node.attributes.keys() and self.node.attributes["class"] == "links":
      commands.append(
          DrawRect(x1=self.x, y1=self.y, x2=self.x + self.width, y2=self.y + self.height,
                   color="gray"))
    if self.layout_mode() == LayoutMode.INLINE:
      for x, y, word, font in self.display_list:
        commands.append(DrawText(x1=x, y1=y, text=word, font=font))
    return commands

class DocumentLayout:
  def __init__(self, viewport_width: int, node: Node):
    self.viewport_width: int = viewport_width
    self.node: Node = node
    self.parent: None = None
    self.children: list[BlockLayout] = []
    self.x: int | None = None
    self.y: int | None = None
    self.width: int | None = None
    self.height: int | None = None

  def layout(self):
    child = BlockLayout(
      node=self.node,
      parent=self,
      previous=None,
    )
    self.children.append(child)
    self.width = self.viewport_width - 2 * HSTEP
    self.x = HSTEP
    self.y = VSTEP
    child.layout()
    self.height = child.height

  def paint(self) -> Commands:
    return []

def paint_tree(layout_object: DocumentLayout | BlockLayout,
               commands: Commands):
  commands.extend(layout_object.paint())

  for child in layout_object.children:
    paint_tree(child, commands)
