class CacheControl:
  def __init__(self, raw: str):
    assert(raw.__len__() > 0)
    directives = raw.split(",")
    self.no_store = False
    self.max_age = 0
    for directive in directives:
      if "=" in directive:
        key, value = directive.split("=")
        if key == "max-age":
          self.max_age = int(value)
      else:
        if directive == "no-store":
          self.no_store = True
