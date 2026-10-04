#!/usr/bin/env python3
"""Refresh the recent-papers list on index.html from INSPIRE-HEP.

Run from this folder:  python3 update_publications.py
It rewrites only the part of index.html between the RECENT markers.
"""
import html
import json
import re
import urllib.request

AUTHOR_BAI = "Andrzej.Pokraka.1"
MY_LAST_NAME = "Pokraka"

# The home page lists this many of the most recent papers.
N_RECENT = 5
HOME = "index.html"

# Extra links shown next to specific papers, keyed by arXiv number.
EXTRA_LINKS = {
    "2603.25703": [("https://frwcoaction.ca", "interactive companion")],
    "2606.13627": [("https://frwcoaction.ca", "interactive companion")],
}

FIELDS = ",".join([
    "control_number", "titles", "authors.full_name", "arxiv_eprints",
    "publication_info", "dois", "preprint_date", "document_type", "imprints",
])
URL = ("https://inspirehep.net/api/literature?sort=mostrecent&size=250"
       f"&q=a%20{AUTHOR_BAI}&fields={FIELDS}")


def name(full):
    last, _, first = full.partition(", ")
    return f"{first} {last}".strip()


def authors(m):
    out = []
    for a in m.get("authors", []):
        n = html.escape(name(a["full_name"]))
        out.append(f"<strong>{n}</strong>" if MY_LAST_NAME in a["full_name"] else n)
    return ", ".join(out)


def journal_ref(m):
    for p in m.get("publication_info", []):
        if p.get("journal_title"):
            s = p["journal_title"].replace(".", ". ").replace("  ", " ").strip()
            if p.get("journal_volume"):
                s += f" {p['journal_volume']}"
            if p.get("year"):
                s += f" ({p['year']})"
            page = p.get("artid") or p.get("page_start")
            if page:
                s += f" {page}"
            return s
    return None


def entry(m):
    title = html.escape(m["titles"][0]["title"])
    kind = m.get("document_type", [""])[0]
    tag = {"conference paper": "proceedings", "thesis": "PhD thesis"}.get(kind, "")
    tag_html = f'<span class="tag">{tag}</span>' if tag else ""

    links = []
    ref = journal_ref(m)
    dois = m.get("dois", [])
    if ref and dois:
        links.append(f'<a href="https://doi.org/{dois[0]["value"]}">{html.escape(ref)}</a>')
    elif ref:
        links.append(html.escape(ref))
    arx = m.get("arxiv_eprints", [])
    if arx:
        a = arx[0]["value"]
        links.append(f'<a href="https://arxiv.org/abs/{a}">arXiv:{a}</a>')
        for url, label in EXTRA_LINKS.get(a, []):
            links.append(f'<a href="{url}">{label}</a>')
    links.append(f'<a href="https://inspirehep.net/literature/{m["control_number"]}">INSPIRE</a>')

    return (f'      <li>\n'
            f'        <span class="title">{title}</span>{tag_html}\n'
            f'        <span class="authors">{authors(m)}</span>\n'
            f'        <span class="ref">{" ".join(links)}</span>\n'
            f'      </li>')


def replace_block(path, name, block):
    with open(path) as f:
        text = f.read()
    text = re.sub(rf"(<!-- {name}:START -->).*?(\s*<!-- {name}:END -->)",
                  lambda mm: f"{mm.group(1)}\n{block}{mm.group(2)}", text, flags=re.S)
    with open(path, "w") as f:
        f.write(text)


def main():
    with urllib.request.urlopen(URL) as r:
        hits = [h["metadata"] for h in json.load(r)["hits"]["hits"]]

    papers = [m for m in hits if m.get("arxiv_eprints") and m.get("preprint_date")]
    papers.sort(key=lambda m: m["preprint_date"], reverse=True)
    recent = ["    <ol class=\"recent\">"]
    recent += [entry(m) for m in papers[:N_RECENT]]
    recent.append("    </ol>")
    replace_block(HOME, "RECENT", "\n".join(recent))
    print(f"Wrote {min(N_RECENT, len(papers))} recent papers to {HOME}")


if __name__ == "__main__":
    main()
