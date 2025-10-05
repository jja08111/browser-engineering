class RequestHeader:
  def __init__(self, path: str, host: str):
    self.request = f"GET {path} HTTP/1.1\r\n"
    self._append("Host", host)
    self._append("User-Agent", "MinseongBrowser/1.0")
    self._append("Connection", "keep-alive")
    self._append("Accept-Encoding", "gzip")
    self.request += "\r\n"

  def _append(self, key, value):
    self.request += f"{key}: {value}\r\n"

  def encode(self):
    return self.request.encode("utf8")
