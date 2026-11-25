#!/usr/bin/env python3
"""Fetch reference metadata by DOI and merge it into a paper's refs.json (CSL-JSON).

    python tools/fetch_refs.py _papers/<slug>/dois.txt _papers/<slug>/refs.json

dois.txt has one `citation-key DOI` pair per line (# comments allowed). Entries already in
refs.json are left alone, so hand corrections (sentence-case titles, missing editors, ...)
survive re-runs; delete an entry to fetch it again. References without a DOI are added to
refs.json by hand.
"""
import json
import os
import pathlib
import sys
import time
import urllib.request

# doi.org returns Crossref's own type names for some records; map them to CSL types
TYPES = {"journal-article": "article-journal", "proceedings-article": "paper-conference", "book-chapter": "chapter"}
NAME_PARTS = ("family", "given", "non-dropping-particle", "dropping-particle", "suffix", "literal")
KEEP = ["id", "type", "title", "author", "editor", "issued", "container-title", "volume", "issue", "page",
        "number", "publisher", "publisher-place", "DOI", "URL", "edition", "collection-title", "genre", "status"]


def fetch(doi: str) -> dict:
    # Crossref's "polite pool" wants a contact address; set CROSSREF_MAILTO to provide one
    agent = "sandervandecruys.be paper build"
    if os.environ.get("CROSSREF_MAILTO"):
        agent += f" (mailto:{os.environ['CROSSREF_MAILTO']})"
    req = urllib.request.Request(
        "https://doi.org/" + doi,
        headers={"Accept": "application/vnd.citationstyles.csl+json", "User-Agent": agent},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def clean(key: str, e: dict) -> dict:
    if "published-print" in e:  # APA uses the issue year, not the online-first date
        e["issued"] = e["published-print"]
    e["issued"] = {"date-parts": [e["issued"]["date-parts"][0][:1]]}
    e["id"] = key
    e["type"] = TYPES.get(e["type"], e["type"])
    if e.get("article-number") and not e.get("page"):
        e["number"] = e["article-number"]
    if e.get("DOI", "").lower().startswith("10.48550/arxiv"):  # preprints, whatever type the record claims
        e["type"] = "article"
        e["publisher"] = "arXiv"
        e.pop("container-title", None)
    if isinstance(e.get("container-title"), str):
        e["container-title"] = e["container-title"].replace("&amp;", "&")
    e.pop("URL", None)  # APA links the DOI
    for role in ("author", "editor"):  # keep just the name parts; normalise U+2010 hyphens (Wiley)
        if role in e:
            e[role] = [{k: v.replace("\u2010", "-") for k, v in person.items() if k in NAME_PARTS}
                       for person in e[role]]
            e[role] = [p for p in e[role] if p]  # Crossref sometimes has empty name records
    for k in ("title", "container-title"):
        if isinstance(e.get(k), str):
            e[k] = e[k].replace("\u2010", "-")
    return {k: e[k] for k in KEEP if e.get(k) not in (None, "", [])}


def main() -> None:
    dois_file, refs_file = map(pathlib.Path, sys.argv[1:3])
    refs = json.loads(refs_file.read_text(encoding="utf-8")) if refs_file.exists() else []
    known = {r["id"] for r in refs}
    failed = []
    for line in dois_file.read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        key, doi = line.split()
        if key in known:
            continue
        try:
            refs.append(clean(key, fetch(doi)))
        except Exception as error:  # keep going; a bad DOI shouldn't lose the rest
            failed.append(key)
            print(f"FAILED  {key} ({doi}): {error}")
            continue
        print(f"fetched {key}: {refs[-1].get('title', '')[:70]}")
        time.sleep(0.3)
    refs_file.write_text(json.dumps(refs, ensure_ascii=False, indent=1), encoding="utf-8")
    if failed:
        print(f"{len(failed)} failed (fix the DOI or add by hand): {', '.join(failed)}")
    print("Check titles: APA wants sentence case, Crossref often has title case.")


if __name__ == "__main__":
    main()
