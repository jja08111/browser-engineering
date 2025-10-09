from typing import List
from body import Body

class Text:
  def __init__(self, text: str):
    self.text = text

class Tag:
  def __init__(self, tag: str):
    self.tag = tag

Tokens = List[Text | Tag]

def lex(body: Body) -> Tokens:
  in_tag = False
  index = 0
  content = body.content
  if (body.is_view_source):
    return body.content

  out = []
  buffer = ""
  while (index < content.__len__()):
    c = content[index]
    if c == "<":
      in_tag = True
      if buffer:
        out.append(Text(buffer))
      buffer = ""
    elif c == ">":
      in_tag = False
      out.append(Tag(buffer))
      buffer = ""
    elif content.startswith("&lt;", index):
      buffer += "<"
      index += 3
    elif content.startswith("&gt;", index):
      buffer += ">"
      index += 3
    else:
      buffer += c
    
    index += 1
  if not in_tag and buffer:
    out.append(Text(buffer))
  return out