#!/usr/bin/env python3
"""Render the HTML versions of papers with Pandoc.

Each paper lives in _papers/<slug>/ (paper.md + refs.json). This writes
_includes/papers/<slug>.html (body + references) and _includes/papers/<slug>-toc.html,
which the `paper` layout includes. Run before `jekyll build`:

    python tools/build_papers.py            # all papers
    python tools/build_papers.py <slug>     # one paper
"""
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "_papers"
OUT = ROOT / "_includes" / "papers"
TOOLS = ROOT / "tools"

COMMON = [
    "--from=markdown",
    "--to=html5",
    "--citeproc",  # must come before the Lua filter, which edits the rendered references
    f"--csl={SRC / 'apa.csl'}",
    f"--lua-filter={TOOLS / 'paper.lua'}",
    "--metadata=link-citations:true",
    "--shift-heading-level-by=1",  # sections are h2; the page title is the h1
    "--section-divs",
    "--wrap=none",
    "--toc",
    "--toc-depth=2",
]


def render(paper_dir: pathlib.Path) -> None:
    slug = paper_dir.name
    for template, out in [("paper-body.html", f"{slug}.html"), ("paper-toc.html", f"{slug}-toc.html")]:
        subprocess.run(
            ["pandoc", "paper.md", *COMMON, f"--template={TOOLS / template}", "-o", str(OUT / out)],
            cwd=paper_dir,
            check=True,
        )
    # The TOC is included twice (sidebar and mobile), so drop its ids; the abstract comes from the post.
    toc = OUT / f"{slug}-toc.html"
    html = re.sub(r' id="toc-[^"]*"', "", toc.read_text(encoding="utf-8"))
    html = html.replace("<ul>", '<ul>\n<li><a href="#abstract">Abstract</a></li>', 1)
    toc.write_text(html, encoding="utf-8")
    print(f"rendered {slug}")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    slugs = sys.argv[1:] or sorted(p.name for p in SRC.iterdir() if (p / "paper.md").exists())
    for slug in slugs:
        render(SRC / slug)


if __name__ == "__main__":
    main()
