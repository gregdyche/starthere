#!/usr/bin/env python3
"""Local server for STARTHERE.html.

Same as `python3 -m http.server 8000`, with three differences:
  - binds to 127.0.0.1 only, so nothing on the Wi-Fi can reach it
  - POST /shutdown stops the server (the "Kill proc" button in the banner)
  - PUT /checklist.json saves the Preflight master list (Add and x buttons),
    so edits land in a git-tracked file

Both write endpoints only accept requests whose Host and Origin are this
machine's localhost, so another website open in the browser cannot use them.
"""
import json
import os
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PORT = 8000
LOCAL_HOSTS = {f"localhost:{PORT}", f"127.0.0.1:{PORT}"}
LOCAL_ORIGINS = {f"http://{h}" for h in LOCAL_HOSTS}


MAX_ITEMS = 30
MAX_ITEM_LEN = 200


class Handler(SimpleHTTPRequestHandler):
    def _from_this_page(self):
        return (self.headers.get("Host") in LOCAL_HOSTS
                and self.headers.get("Origin") in LOCAL_ORIGINS)

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

    def log_message(self, *args):
        pass


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    httpd = ThreadingHTTPServer(("127.0.0.1", PORT), partial(Handler, directory=here))
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()
