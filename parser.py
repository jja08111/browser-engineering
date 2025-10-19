from typing import List, Tuple
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
  BLOCK_TAGS = ["p", "li"]
  LIST_OWNER_TAGS = ["ol", "ul"]
  TEXT_FORMATTING_TAGS = ["b", "i"]

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
  
  def close_unfinished_tag(self):
    if len(self.unfinished) == 1:
      return
    node = self.unfinished.pop()
    parent = self.unfinished[-1]
    parent.children.append(node)
  
  def add_tag(self, tag: str):
    if tag.startswith("!"):
      return
    tag, attributes = self.get_attributes(tag)
    self.add_implicit_tags(tag)
    if tag in self.SELF_CLOSING_TAGS:
      parent = self.unfinished[-1]
      node = Element(tag, attributes, parent)
      parent.children.append(node)
      return

    if tag.startswith("/"):
      parent_tag = self.unfinished[-1].tag if self.unfinished else None
      if parent_tag in self.TEXT_FORMATTING_TAGS \
         and parent_tag != tag.split("/")[1]:
        self.close_unfinished_tag()
        self.close_unfinished_tag()
        self.add_tag(parent_tag)
      else:
        self.close_unfinished_tag()
    else:
      parent = self.unfinished[-1] if self.unfinished else None
      if parent and parent.tag in self.BLOCK_TAGS and \
         (tag in self.BLOCK_TAGS or tag in self.LIST_OWNER_TAGS):
        self.close_unfinished_tag()
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
    in_tag = False
    in_comment = False
    in_script = False
    in_attribute = False
    index = 0
    content = self.body.content
    text = ""
    while (index < content.__len__()):
      c = content[index]
      if in_script:
        text += c
        if text.endswith("</script>"):
          text = ""
          in_script = False
      elif in_tag and in_comment:
        text += c
        if c == "\n" or text.endswith("-->"):
          text = ""
          in_tag = False
          in_comment = False
      elif c == "<" and not in_tag:
        in_tag = True
        if text:
          self.add_text(text)
        text = ""
      elif c == ">" and in_tag and not in_attribute:
        in_tag = False
        if text.startswith("script"):
          in_script = True
        else:
          self.add_tag(text)
        text = ""
      elif c == "\"" and in_tag:
        in_attribute = not in_attribute
      elif content.startswith("&lt;", index):
        self.add_text("<")
        index += 3
      elif content.startswith("&gt;", index):
        self.add_text(">")
        index += 3
      else:
        text += c
        if text == "!--":
          in_comment = True
      
      index += 1
    if not in_tag and text:
      self.add_text(text)
    return self.finish()

class ViewSourceHTMLParser(HTMLParser):
  def add_text(self, text: str):
    super().add_tag("pre")
    super().add_tag("b")
    super().add_text(text)
    super().add_tag("/b")
    super().add_tag("/pre")

  def add_tag(self, tag: str):
    if tag.startswith("/"):
      super().add_text(f"<{tag}>")
    else:
      super().add_text(f"<{tag}>")
  
  def parse(self) -> Node:
    super().add_tag("html")
    super().add_tag("body")
    return super().parse()

def create_html_parser(body: Body) -> HTMLParser:
  if body.is_view_source:
    return ViewSourceHTMLParser(body)
  return HTMLParser(body)
