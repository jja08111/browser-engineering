import time
from body import Body

class Cache:
  def __init__(self, body: Body, max_age: int):
    self.body = body
    self.expired_at = time.time() + max_age
