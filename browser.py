import socket
import ssl
import os

class RequestHeader:
  def __init__(self, path: str, host: str):
    self.request = f"GET {path} HTTP/1.1\r\n"
    self._append("Host", host)
    self._append("User-Agent", "MinseongBrowser/1.0")
    self._append("Connection", "close")
    self.request += "\r\n"

  def _append(self, key, value):
    self.request += f"{key}: {value}\r\n"

  def encode(self):
    return self.request.encode("utf8")

class URL:
  def __init__(self, url: str):
    url = self._ensure_scheme(url)

    self.scheme, url = url.split("://", 1)
    if self.scheme == "http":
      self.port = 80
    elif self.scheme == "https":
      self.port = 443
    elif self.scheme == "file":
      self.path = url
      return

    if "/" not in url:
      url = url + "/"
    self.host, url = url.split("/", 1)
    self.path = "/" + url

    if ":" in self.host:
      self.host, port = self.host.split(":", 1)
      self.port = int(port)

  def _ensure_scheme(self, url: str) -> str:
    if url in "://":
      return url
    return f"file://{url}"

  def _open_file_path(self, allowed_root: str = None) -> str:
    if allowed_root:
      allowed_root = os.path.realpath(allowed_root)
      if not os.path.commonpath([allowed_root, self.path]) == allowed_root:
        raise PermissionError("access outside allowed root")

    if not os.path.exists(self.path):
      raise FileNotFoundError(self.path)
    if not os.path.isfile(self.path):
      raise IsADirectoryError(self.path)

    with open(self.path, "rb") as f:
      return f.read().decode("utf8")

  def request(self) -> str:
    if self.scheme == "file":
      return self._open_file_path()

    s = socket.socket(
      family=socket.AF_INET,
      type=socket.SOCK_STREAM,
      proto=socket.IPPROTO_TCP,
    )
    s.connect((self.host, self.port))
    if (self.scheme == "https"):
      ctx = ssl.create_default_context()
      s = ctx.wrap_socket(s, server_hostname=self.host)

    header = RequestHeader(path=self.path, host=self.host)
    s.send(header.encode())

    # TODO: Replace hardcoded encoding by parsing header `Content-Type`
    response = s.makefile("r", encoding="utf8", newline="\r\n")

    statusline = response.readline()
    version, status, explanation = statusline.split(" ", 2)
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    print(f"version: {version}")
    print(f"status: {status}")
    print(f"explanation: {explanation}")

    response_headers = {}
    while True:
      line = response.readline()
      if line == "\r\n":
        break
      header, value = line.split(":", 1)
      response_headers[header.casefold()] = value.strip()
    assert "content-encoding" not in response_headers

    body = response.read()
    s.close()
    return body

def show(body: str):
  in_tag = False
  for c in body:
    if c == "<":
      in_tag = True
    elif c == ">":
      in_tag = False
    elif not in_tag:
      print(c, end="")

def load(url):
  body = url.request()
  show(body)

if __name__ == "__main__":
  import sys
  load(URL(sys.argv[1]))