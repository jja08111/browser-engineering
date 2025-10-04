import socket
import ssl
import os
import time
from typing import Dict

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

class Status:
  def __init__(self, code: str):
    self.code = int(code)

  def is_redirect(self) -> bool:
    return 300 <= self.code < 400

class Body:
  def __init__(self, content: str, is_view_source: bool=False):
    self.content = content
    self.is_view_source = is_view_source

class Cache:
  def __init__(self, body: Body, max_age: int):
    self.body = body
    self.expired_at = time.time() + max_age

class URL:
  def __init__(self, url: str):
    self.caches: Dict[str, Cache] = dict()
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

  def _get_url(self) -> str:
    assert(self.scheme)
    assert(self.host)
    assert(self.path)
    assert(self.port)
    return f"{self.scheme}://{self.host}:{self.port}/{self.path}"

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

  def _resolve_location(self, location: str) -> str:
    # already absolute URL (has scheme)
    if "://" in location:
      return location
    # scheme-relative: //host/path
    if location.startswith("//"):
      return f"{self.scheme}:{location}"
    # absolute-path on same origin: /path...
    if location.startswith("/"):
      return f"{self.scheme}://{self.host}:{self.port}/{location}"
    # relative path (no leading slash) -> join with base dir of self.path
    # self.path is like "/dir/page" or "/page"
    base_dir = self.path.rsplit("/", 1)[0]  # '/dir' or ''
    if base_dir == "":
      base_dir = "/"
    # ensure single slash between
    if base_dir.endswith("/"):
      joined = f"{base_dir}{location}"
    else:
      joined = f"{base_dir}/{location}"
    return f"{self.scheme}://{self.host}:{self.port}/{joined}"

  def request(self, redirect_count: int = 0) -> Body:
    if self.scheme == "file":
      return Body(content=self._open_file_path())
    elif self.scheme == "data":
      return Body(content=self.data)

    # TODO: Move cache to local file?
    url = self._get_url()
    cache = self.caches.get(url)
    if not cache is None:
      if cache.expired_at > time.time():
        return cache.body
      else:
        self.caches.pop(url)

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
    print(f"statusline: {statusline}")
    version, status_code, explanation = statusline.split(" ", 2)
    status = Status(code=status_code)
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

    if redirect_count < 5 and status.is_redirect():
      location = response_headers.get("location")
      if location is None:
        raise RuntimeError("Redirect status, but no Location header")
      location = self._resolve_location(location)
      try:
        self.socket.close()
        self.socket = None
      except Exception:
        pass
      self.__init__(location)
      return self.request(redirect_count=redirect_count + 1)

    content_length = response_headers["content-length"]
    raw_body = response.read(int(content_length))
    body = Body(content=raw_body, is_view_source=self.is_view_source)

    cache_control_raw = response_headers.get("cache-control")
    if not cache_control_raw is None:
      cache_control = CacheControl(raw=cache_control_raw)
      if not cache_control.no_store and cache_control.max_age > 0:
        self.caches[url] = Cache(
          body=body, 
          max_age=cache_control.max_age
        )

    return body

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