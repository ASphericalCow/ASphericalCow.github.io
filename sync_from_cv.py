#!/usr/bin/env python3
"""Rebuild the recorded-talks list on notes.html from the LaTeX CV, and copy the CV PDF.

Run from this folder:  python3 sync_from_cv.py
Only talks with a recording link (\\talk{date}[url]{...}{...}) are listed.
It rewrites only the part of notes.html between the TALKS markers.
"""
import html
import re
import shutil
from pathlib import Path

CV_DIR = Path.home() / "My Drive/Physics/CV/CV"
CV_TEX = CV_DIR / "CV_Pokraka.tex"
CV_PDF = CV_DIR / "CV_Pokraka.pdf"
PAGE = Path("notes.html")

ACCENTS = {r'\"o': "ö", r'\"u': "ü", r'\"a': "ä", r"\'e": "é", r"\'a": "á",
           r"\'i": "í", r"\`e": "è", r"\'E": "É"}


def full_version(tex):
    """Keep the full-CV branch of every \\ifbrief ... [\\else ...] \\fi."""
    tex = tex[tex.index(r"\begin{document}"):]
    out, stack = [], []          # stack entries: True while in the brief-only branch
    for tok in re.split(r"(\\ifbrief|\\else|\\fi\b)", tex):
        if tok == r"\ifbrief":
            stack.append(True)
        elif tok == r"\else" and stack:
            stack[-1] = False
        elif tok == r"\fi" and stack:
            stack.pop()
        elif not any(stack):
            out.append(tok)
    return "".join(out)


def to_html(s):
    """Convert the small amount of LaTeX used in CV entries to HTML."""
    s = " ".join(s.split())
    for k, v in ACCENTS.items():
        s = s.replace(k + "{}", v).replace("{" + k + "}", v).replace(k, v)
    s = html.escape(s, quote=False)
    s = re.sub(r"\\href\{([^}]*)\}\{([^}]*)\}", r'<a href="\1">\2</a>', s)
    s = re.sub(r"\\emph\{([^}]*)\}", r"<em>\1</em>", s)
    s = s.replace(r"\bsep", " · ").replace("--", "–").replace("~", " ")
    s = s.replace(r"\ ", " ").replace("$", "").replace("{", "").replace("}", "")
    return re.sub(r"\s+·\s+", " · ", s).strip()


def talks(tex):
    pat = re.compile(r"\\talk\{([^}]*)\}(?:\[([^\]]*)\])?\s*\{([^}]*)\}\s*\{(.*?)\}\s*(?=\\talk|%|\\vspace|\\subsection|$)", re.S)
    items = []
    for date, url, title, event in pat.findall(tex):
        if not url:
            continue
        t = f'<a href="{url}">{to_html(title)}</a>'
        items.append(f'      <li>\n'
                     f'        <span class="title">{t}</span>\n'
                     f'        <span class="ref">{to_html(event)} · {date}</span>\n'
                     f'      </li>')
    return "    <ul class=\"plain\">\n" + "\n".join(items) + "\n    </ul>", len(items)


def replace(text, name, block):
    return re.sub(rf"(<!-- {name}:START -->).*?(\s*<!-- {name}:END -->)",
                  lambda mm: f"{mm.group(1)}\n{block}{mm.group(2)}", text, flags=re.S)


def main():
    tex = full_version(CV_TEX.read_text())
    talk_block, n = talks(tex)
    text = PAGE.read_text()
    text = replace(text, "TALKS", talk_block)
    PAGE.write_text(text)
    shutil.copy(CV_PDF, "cv.pdf")
    print(f"Wrote {n} recorded talks to {PAGE}; copied cv.pdf")


if __name__ == "__main__":
    main()
