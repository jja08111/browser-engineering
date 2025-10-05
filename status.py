class Status:
  def __init__(self, code: str):
    self.code = int(code)

  def is_redirect(self) -> bool:
    return 300 <= self.code < 400
