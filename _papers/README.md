# Paper sources

Online (HTML) versions of publications. Each paper is a folder:

```
_papers/<slug>/
  paper.md     body text in Pandoc Markdown, citations as [@key]
  refs.json    references (CSL-JSON)
```

Figures go in `images/papers/<slug>/`. `apa.csl` is the APA 7 citation style used for all papers.

The paper's post in `_posts/` uses `layout: paper` and `paper: <slug>`. Its front matter holds the
title, authors (`author_list`, `affiliations`), journal, `year`, `volume`, `article_number`, `doi`
and the PDF `link`; its content is the abstract.

## Building

`tools/build_papers.py` renders every `paper.md` with Pandoc (3.x) into `_includes/papers/`, which the
layout includes. GitHub Actions does this before the Jekyll build (`.github/workflows/site.yml`). Locally:

```
python tools/build_papers.py
```

## Adding a paper

1. Write `paper.md` from the published version (the PDF), with section headings as `#` and figures
   as `![**Figure 1.** caption](/images/papers/<slug>/fig1.webp){#fig-1}`. Link figures from the text
   with `[Figure 1](#fig-1)`.
2. List the references that have a DOI in `dois.txt` (`key DOI` per line) and run
   `python tools/fetch_refs.py _papers/<slug>/dois.txt _papers/<slug>/refs.json`; add the rest by hand.
   Check titles are in sentence case.
3. "Of special/outstanding interest" notes go in the `annotations` metadata of `paper.md`.
