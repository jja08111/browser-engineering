from typing import List, Mapping, Tuple
from body import Body

class Text:
  def __init__(self, text: str, parent):
    self.text: str = text
    self.children: List[Node] = []
    self.parent: Node = parent
  
  def __repr__(self) -> str:
    return repr(self.text)

Attributes = dict[str, str]

class Element:
  def __init__(self, tag: str, attributes: Attributes, parent):
    self.tag: str = tag
    self.children: List[Node] = []
    self.attributes: Attributes = attributes
    self.parent: Node = parent

  def __repr__(self) -> str:
    return "<" + self.tag + ">"

Node = Text | Element
Nodes = List[Node]

class HTMLParser:
  SELF_CLOSING_TAGS = [
    "area", "base", "br", "col", "embed", "hr", "img", "input",
    "link", "meta", "param", "source", "track", "wbr",
  ]
  HEAD_TAGS = [
    "base", "basefont", "bgsound", "noscript",
    "link", "meta", "title", "style", "script"
  ]

  def __init__(self, body: Body) -> None:
    self.body = body
    self.unfinished: List[Element] = []
  
  def get_attributes(self, text: str) -> Tuple[str, Attributes]:
    parts = text.split()
    tag = parts[0].casefold()
    attributes = {}
    for attrpair in parts[1:]:
      if "=" in attrpair:
        key, value = attrpair.split("=", 1)
        attributes[key.casefold()] = value
        if len(value) > 2 and value[0] in ["'", "\""]:
          value = value[1:-1]
      else:
        attributes[attrpair.casefold()] = ""
    return tag, attributes
  
  def add_implicit_tags(self, tag: str):
    while True:
      open_tags = [node.tag for node in self.unfinished]
      if open_tags == [] and tag != "html":
        self.add_tag("html")
      elif open_tags == ["html"] \
           and tag not in ["head", "body", "/html"]:
        if tag in self.HEAD_TAGS:
          self.add_tag("head")
        else:
          self.add_tag("body")
      elif open_tags == ["html", "head"] and \
           tag not in ["/head"] + self.HEAD_TAGS:
        self.add_tag("/head")
      else:
        break
  
  def add_text(self, text: str):
    if text.isspace():
      return
    self.add_implicit_tags(None)

    parent = self.unfinished[-1]
    node = Text(text, parent)
    parent.children.append(node)
  
  def add_tag(self, tag: str):
    tag, attributes = self.get_attributes(tag)
    if tag.startswith("!"):
      return
    self.add_implicit_tags(tag)
    if tag in self.SELF_CLOSING_TAGS:
      parent = self.unfinished[-1]
      node = Element(tag, attributes, parent)
      parent.children.append(node)

    if tag.startswith("/"):
      if len(self.unfinished) == 1:
        return
      node = self.unfinished.pop()
      parent = self.unfinished[-1]
      parent.children.append(node)
    else:
      parent = self.unfinished[-1] if self.unfinished else None
      node = Element(tag, attributes, parent)
      self.unfinished.append(node)

  def finish(self) -> Node:
    if not self.unfinished:
      self.add_implicit_tags(None)
    while len(self.unfinished) > 1:
      node = self.unfinished.pop()
      parent = self.unfinished[-1]
      parent.children.append(node)
    return self.unfinished.pop()

  def parse(self) -> Node:
    if (self.body.is_view_source):
      return self.body.content

    in_tag = False
    index = 0
    content = self.body.content
    text = ""
    while (index < content.__len__()):
      c = content[index]
      if c == "<":
        in_tag = True
        if text:
          self.add_text(text)
        text = ""
      elif c == ">":
        in_tag = False
        self.add_tag(text)
        text = ""
      elif content.startswith("&lt;", index):
        self.add_text("<")
        index += 3
      elif content.startswith("&gt;", index):
        self.add_text(">")
        index += 3
      else:
        text += c
      
      index += 1
    if not in_tag and text:
      self.add_text(text)
    return self.finish()

def print_tree(node: Node, indent=0):
  print(" " * indent, node)
  for child in node.children:
    print_tree(child, indent + 2)