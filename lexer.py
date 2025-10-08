from body import Body

def lex(body: Body) -> str:
  in_tag = False
  index = 0
  content = body.content
  if (body.is_view_source):
    return body.content

  text = ""
  while (index < content.__len__()):
    c = content[index]
    if c == "<":
      in_tag = True
    elif c == ">":
      in_tag = False
    elif content.startswith("&lt;", index):
      text += "<"
      index += 3
    elif content.startswith("&gt;", index):
      text += ">"
      index += 3
    elif not in_tag:
      text += c
    index += 1
  return text