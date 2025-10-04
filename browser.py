import socket
import ssl
import os

class RequestHeader:
  def __init__(self, path: str, host: str):
    self.request = f"GET {path} HTTP/1.1\r\n"
    self._append("Host", host)
    self._append("User-Agent", "MinseongBrowser/1.0")
    self._append("Connection", "keep-alive")
    self.request += "\r\n"

  def _append(self, key, value):
    self.request += f"{key}: {value}\r\n"

  def encode(self):
    return self.request.encode("utf8")

class Body:
  def __init__(self, content: str, is_view_source: bool):
    self.content = content
    self.is_view_source = is_view_source

class URL:
  def __init__(self, url: str):
    self.socket = None
    self.is_view_source = False
    if url.startswith("data:"):
      self.scheme, url = url.split(":", 1)
      url, self.data = url.split(",", 1)
      self.data += "\r\n"
      if ";" in url:
        self.media_type, url = url.split(";", 1)
      else:
        self.media_type = url
      assert(self.media_type == "text/html")
      return
    if url.startswith("view-source"):
      _, url = url.split(":", 1)
      self.is_view_source = True

    url = self._ensure_scheme(url)
    print(url)
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
    if "://" in url:
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

  def request(self) -> Body:
    if self.scheme == "file":
      return self._open_file_path()
    elif self.scheme == "data":
      return self.data

    if self.socket is None:
      self.socket = socket.socket(
        family=socket.AF_INET,
        type=socket.SOCK_STREAM,
        proto=socket.IPPROTO_TCP,
      )
      self.socket.connect((self.host, self.port))
      if (self.scheme == "https"):
        ctx = ssl.create_default_context()
        self.socket = ctx.wrap_socket(self.socket, server_hostname=self.host)

    header = RequestHeader(path=self.path, host=self.host)
    self.socket.send(header.encode())

    # TODO: Replace hardcoded encoding by parsing header `Content-Type`
    response = self.socket.makefile("r", encoding="utf8", newline="\r\n")

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

    content_length = response_headers["content-length"]
    body = response.read(int(content_length))
    return Body(content=body, is_view_source=self.is_view_source)

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