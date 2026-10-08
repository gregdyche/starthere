#!/usr/bin/env python3
"""Local server for STARTHERE.html.

Same as `python3 -m http.server 8000`, with three differences:
  - binds to 127.0.0.1 only, so nothing on the Wi-Fi can reach it
  - POST /shutdown stops the server (the "Kill proc" button in the banner)
  - PUT /checklist.json saves the Preflight master list (Add and x buttons),
    so edits land in a git-tracked file
  - GET /checklists?q=... searches the checklist index (Checklists card), and
    POST /checklists/open opens one of them on this Mac. Both use the reader
    in the Stacks repo (STACKS_TOOLS, default ~/repos/stacks/tools); open
    takes an index number, never a path, so only listed files can be opened.
  - GET /brief renders the daily brief markdown (BRIEF_PATH, default
    ~/daily-brief.md) as an HTML page, so it is read in the browser. The
    brief never enters this repo; it is read from disk on each request.
  - GET /crm renders the newest CRM_Briefing_YYYY-MM-DD.md in CRM_DIR
    (default ~/Documents/Claude/Projects/My CRM) the same way.

All write and open endpoints only accept requests whose Host and Origin are this
machine's localhost, so another website open in the browser cannot use them.
"""
import glob
import html
import importlib.util
import json
import os
import threading
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

PORT = 8000
LOCAL_HOSTS = {f"localhost:{PORT}", f"127.0.0.1:{PORT}"}
LOCAL_ORIGINS = {f"http://{h}" for h in LOCAL_HOSTS}


STACKS_TOOLS = os.environ.get("STACKS_TOOLS", os.path.expanduser("~/repos/stacks/tools"))
# Fields the page needs; the absolute path stays on the server.
PUBLIC_FIELDS = ("id", "title", "path", "type", "when", "section", "exists",
                 "revised", "age_days", "stale", "snippet",
                 "github_url", "ahead", "behind", "dirty")


def _checklists():
    """The Stacks reader, loaded fresh each call so index edits show on reload.
    None when the Stacks repo is not on this machine."""
    src = os.path.join(STACKS_TOOLS, "checklists.py")
    if not os.path.isfile(src):
        return None
    spec = importlib.util.spec_from_file_location("checklists", src)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


BRIEF_PATH = os.environ.get("BRIEF_PATH", os.path.expanduser("~/daily-brief.md"))
CRM_DIR = os.environ.get("CRM_DIR", os.path.expanduser("~/Documents/Claude/Projects/My CRM"))


def _newest_crm_briefing():
    """Newest CRM_Briefing_YYYY-MM-DD.md by the date in its name, or None."""
    found = sorted(glob.glob(os.path.join(glob.escape(CRM_DIR), "CRM_Briefing_*.md")))
    return found[-1] if found else None


# marked (pinned) renders the markdown in the browser; tables included.
BRIEF_PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
  :root { --ink:#1b2a3a; --bg:#f7f5ef; --line:#d9d4c7; --link:#1d5fa8; }
  @media (prefers-color-scheme: dark) {
    :root { --ink:#e6e2d8; --bg:#14181d; --line:#333a42; --link:#7fb2ec; }
  }
  body { background:var(--bg); color:var(--ink); margin:0;
         font:16px/1.55 -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
  main { max-width:900px; margin:0 auto; padding:24px 16px 64px; }
  a { color:var(--link); }
  h1 { font-size:1.6rem; } h2 { margin-top:2rem; border-bottom:1px solid var(--line); }
  table { border-collapse:collapse; width:100%; font-size:.92rem; display:block; overflow-x:auto; }
  th, td { border:1px solid var(--line); padding:6px 8px; text-align:left; vertical-align:top; }
  .meta { font-size:.8rem; opacity:.7; }
</style></head><body><main>
<div class="meta">__META__</div>
<div id="brief">Loading...</div>
</main>
<script src="https://cdn.jsdelivr.net/npm/marked@12.0.2/marked.min.js"></script>
<script>
const md = __MD__;
document.getElementById('brief').innerHTML = marked.parse(md);
document.querySelectorAll('#brief a').forEach(a => a.target = '_blank');
</script></body></html>"""


MAX_ITEMS = 30
MAX_ITEM_LEN = 200


class Handler(SimpleHTTPRequestHandler):
    def _from_this_page(self):
        return (self.headers.get("Host") in LOCAL_HOSTS
                and self.headers.get("Origin") in LOCAL_ORIGINS)

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/brief":
            self._markdown_page(BRIEF_PATH, "Daily Brief")
            return
        if url.path == "/crm":
            self._markdown_page(_newest_crm_briefing(), "CRM Briefing",
                                missing=f"No CRM_Briefing_*.md found in `{CRM_DIR}`.")
            return
        if url.path != "/checklists":
            return super().do_GET()
        if self.headers.get("Host") not in LOCAL_HOSTS:
            self.send_error(403)
            return
        cl = _checklists()
        if cl is None:
            self._json(404, {"error": f"no checklist reader at {STACKS_TOOLS}"})
            return
        query = parse_qs(url.query).get("q", [""])[0][:200]
        items = cl.search(query)
        self._json(200, {"stale_days": cl.STALE_DAYS, "query": query,
                         "items": [{k: i[k] for k in PUBLIC_FIELDS if k in i}
                                   for i in items]})

    def _markdown_page(self, path, title, missing=None):
        if self.headers.get("Host") not in LOCAL_HOSTS:
            self.send_error(403)
            return
        try:
            if path is None:
                raise OSError
            with open(path, encoding="utf-8") as f:
                md = f.read()
            stamp = time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(path)))
            meta = f"{html.escape(path)}, saved {stamp}"
        except OSError:
            md, meta = missing or f"No file found at `{path}`.", "missing"
        # json.dumps alone would let "</script>" in the markdown close the tag
        page = (BRIEF_PAGE.replace("__TITLE__", title).replace("__META__", meta)
                .replace("__MD__", json.dumps(md).replace("</", "<\\/")))
        body = page.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_PUT(self):
        if self.path != "/checklist.json":
            self.send_error(404)
            return
        if not self._from_this_page():
            self.send_error(403)
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length > 16384:
                raise ValueError
            items = json.loads(self.rfile.read(length))["items"]
            if (not isinstance(items, list) or len(items) > MAX_ITEMS
                    or not all(isinstance(t, str) and 0 < len(t) <= MAX_ITEM_LEN
                               for t in items)):
                raise ValueError
        except (ValueError, KeyError, TypeError):
            self.send_error(400)
            return
        path = os.path.join(self.directory, "checklist.json")
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump({"items": items}, f, indent=2)
            f.write("\n")
        os.replace(tmp, path)  # atomic: a crash never leaves half a file
        self.send_response(204)
        self.end_headers()

    def do_POST(self):
        if self.path == "/checklists/open":
            self._open_checklist()
            return
        if self.path != "/shutdown":
            self.send_error(404)
            return
        if not self._from_this_page():
            self.send_error(403)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"stopping\n")
        # shutdown() blocks until serve_forever() returns, so call it off-thread
        threading.Thread(target=self.server.shutdown).start()

    def _open_checklist(self):
        if not self._from_this_page():
            self.send_error(403)
            return
        cl = _checklists()
        try:
            length = int(self.headers.get("Content-Length", 0))
            if cl is None or length > 256:
                raise ValueError
            wanted = json.loads(self.rfile.read(length))["id"]
            item = next(i for i in cl.load() if i["id"] == wanted and i["exists"])
        except (ValueError, KeyError, TypeError, StopIteration):
            self.send_error(400)
            return
        cl.open_item(item)
        self.send_response(204)
        self.end_headers()

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    httpd = ThreadingHTTPServer(("127.0.0.1", PORT), partial(Handler, directory=here))
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
