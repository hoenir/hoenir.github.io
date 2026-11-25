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
    "--citeproc",
    f"--csl={SRC / 'apa.csl'}",
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
    fold_references(OUT / f"{slug}.html")
    if notes_before_references(OUT / f"{slug}.html"):
        html = html.replace('<li><a href="#references">', '<li><a href="#notes">Notes</a></li>\n<li><a href="#references">', 1)
        toc.write_text(html, encoding="utf-8")
    print(f"rendered {slug}")


def fold_references(path: pathlib.Path) -> None:
    """Fold the reference list into a <details> so it doesn't add to the page length.
    paper.js opens it when a citation link points into it."""
    html = path.read_text(encoding="utf-8")
    start = html.find('<div id="refs"')
    if start < 0:
        return
    end = html.index("</section>", start)
    count = html.count('class="csl-entry"', start, end)
    html = (html[:start]
            + f'<details class="refs-fold">\n<summary><span class="refs-show">Show all {count} references</span>'
            + '<span class="refs-hide">Hide references</span></summary>\n'
            + html[start:end] + "</details>\n" + html[end:])
    path.write_text(html, encoding="utf-8")


def notes_before_references(path: pathlib.Path) -> bool:
    """Pandoc puts footnotes at the very end; show them as a "Notes" section before the references."""
    html = path.read_text(encoding="utf-8")
    m = re.search(r'<section id="footnotes"[^>]*>\n<hr />\n(.*?)</section>\n', html, flags=re.S)
    if not m or '<section id="references"' not in html:
        return False
    notes = f'<section id="notes" class="level2 footnotes" role="doc-endnotes">\n<h2>Notes</h2>\n{m.group(1)}</section>\n'
    html = html.replace(m.group(0), "")
    anchor = '<div class="backmatter">' if '<div class="backmatter">' in html else '<section id="references"'
    html = html.replace(anchor, notes + anchor, 1)
    path.write_text(html, encoding="utf-8")
    return True


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    slugs = sys.argv[1:] or sorted(p.name for p in SRC.iterdir() if (p / "paper.md").exists())
    for slug in slugs:
        render(SRC / slug)


if __name__ == "__main__":
    main()
