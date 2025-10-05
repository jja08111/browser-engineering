import socket
import ssl
import os
import time
import gzip
from typing import Dict
from body import Body
from cache import Cache
from cache_control import CacheControl
from request_header import RequestHeader
from status import Status

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
    response = self.socket.makefile("rb")

    statusline = response.readline()
    print(f"statusline: {statusline}")
    version, status_code, explanation = statusline.split(b" ", 2)
    status = Status(code=status_code)
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
    print(f"version: {version}")
    print(f"status: {status}")
    print(f"explanation: {explanation}")

    response_headers = {}
    while True:
      line = response.readline()
      if line == b"\r\n":
        break
      header, value = line.split(b":", 1)
      header = header.decode("utf8")
      value = value.decode("utf8")
      response_headers[header.casefold()] = value.strip()

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
    content_encoding = response_headers["content-encoding"]
    raw_body = response.read(int(content_length))
    if content_encoding == "gzip":
      raw_body = gzip.decompress(raw_body)
    print(raw_body.decode("utf8"))
    body = Body(content=raw_body.decode("utf8"), is_view_source=self.is_view_source)

    cache_control_raw = response_headers.get("cache-control")
    if not cache_control_raw is None:
      cache_control = CacheControl(raw=cache_control_raw)
      if not cache_control.no_store and cache_control.max_age > 0:
        self.caches[url] = Cache(
          body=body, 
          max_age=cache_control.max_age
        )

    return body