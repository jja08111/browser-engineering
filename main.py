from body import Body
from url import URL

def show(body: Body):
  in_tag = False
  index = 0
  content = body.content
  if (body.is_view_source):
    print(body.content)
    return

  while (index < content.__len__()):
    c = content[index]
    if c == "<":
      in_tag = True
    elif c == ">":
      in_tag = False
    elif content.startswith("&lt;", index):
      print("<", end="")
      index += 3
    elif content.startswith("&gt;", index):
      print(">", end="")
      index += 3
    elif not in_tag:
      print(c, end="")
    index += 1

def load(url):
  body = url.request()
  show(body)

  body = url.request()
  show(body)

if __name__ == "__main__":
  import sys
  load(URL(sys.argv[1]))
