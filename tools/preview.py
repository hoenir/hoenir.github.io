#!/usr/bin/env python3
"""Preview a branch locally, exactly as GitHub builds it (no Ruby or Jekyll needed).

Push the branch, wait for its "Site" build to finish, then run:

    python tools/preview.py                 # the branch you have checked out
    python tools/preview.py <branch>        # another branch

This downloads the built site from the branch's latest successful build (via the GitHub
CLI, `gh`) and serves it at http://localhost:4000. Press Ctrl+C to stop.
"""
import http.server
import json
import os
import pathlib
import subprocess
import sys
import tempfile

REPO = "hoenir/hoenir.github.io"
PORT = 4000


def gh(*args: str) -> str:
    return subprocess.run(["gh", *args], check=True, capture_output=True, text=True).stdout


def main() -> None:
    branch = sys.argv[1] if len(sys.argv) > 1 else subprocess.run(
        ["git", "branch", "--show-current"], check=True, capture_output=True, text=True).stdout.strip()
    if branch == "master":
        sys.exit("master is deployed straight to the live site, which is its preview: https://sandervandecruys.be")
    runs = json.loads(gh("run", "list", "-R", REPO, "--branch", branch, "--workflow", "site.yml",
                         "--status", "success", "--limit", "1", "--json", "databaseId,headSha,createdAt"))
    if not runs:
        sys.exit(f"No successful build for '{branch}' yet. Push it and wait for the Site workflow to finish.")
    run = runs[0]
    site = pathlib.Path(tempfile.mkdtemp(prefix="site-preview-"))
    gh("run", "download", str(run["databaseId"]), "-R", REPO, "-n", "site", "-D", str(site))
    print(f"Preview of {branch} @ {run['headSha'][:7]} (built {run['createdAt']})", flush=True)
    print(f"Open http://localhost:{PORT}  (Ctrl+C to stop)", flush=True)

    class Handler(http.server.SimpleHTTPRequestHandler):
        # GitHub Pages serves /about as about.html or about/index.html
        def send_head(self):
            path = self.translate_path(self.path)
            if not os.path.exists(path) and os.path.exists(path + ".html"):
                self.path = self.path.split("?")[0] + ".html"
            return super().send_head()

        def log_message(self, *args):
            pass

    os.chdir(site)
    try:
        http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
