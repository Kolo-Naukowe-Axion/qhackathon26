"""Build one portable HTML file from the learning-guide source.

Build-only packages: markdown, latex2mathml (recorded in requirements-build.txt).
python3 -m pip install markdown latex2mathml
python3 docs/learning-methods/build.py
"""
from pathlib import Path
import html
import json
import re

import markdown
from latex2mathml.converter import convert

HERE = Path(__file__).resolve().parent
source = (HERE / "guide.md").read_text()
fragments = []
equation_count = 0


def block_math(match):
    global equation_count
    equation_count += 1
    tex = match.group(1).strip()
    if r'\begin{aligned}' in tex:
        # Native browsers do not honour MathML mspace linebreaks emitted by
        # some converters. Build a real two-column alignment table instead.
        inner = tex.replace(r'\begin{aligned}', '').replace(r'\end{aligned}', '').strip()
        rows = []
        for row in re.split(r'\\\\', inner):
            cells = []
            for cell in row.strip().split('&'):
                converted = convert(cell.strip() or '{}', display='inline')
                cells.append('<mtd>'+re.sub(r'^<math[^>]*>|</math>$', '', converted)+'</mtd>')
            rows.append('<mtr>'+''.join(cells)+'</mtr>')
        mathml = '<math xmlns="http://www.w3.org/1998/Math/MathML" display="block"><mtable columnalign="right left" columnspacing="0.3em" rowspacing="0.6em">'+''.join(rows)+'</mtable></math>'
    else:
        mathml = convert(tex, display="block")
    fragment = (f'<figure class="equation" id="eq-{equation_count}"><div class="math-scroll" tabindex="0" '
                f'aria-label="Equation {equation_count}">{mathml}</div>'
                f'<a class="eq-number" href="#eq-{equation_count}" aria-label="Link to equation {equation_count}">({equation_count})</a></figure>')
    fragments.append(fragment)
    return f'\n\n<div data-math-fragment="{len(fragments)-1}"></div>\n\n'


def inline_math(match):
    tex = match.group(1)
    fragments.append('<span class="inline-math">'+convert(tex, display="inline")+'</span>')
    return f'MATHFRAGMENTTOKEN{len(fragments)-1}ENDTOKEN'


source = re.sub(r'\$\$\s*\n(.*?)\n\s*\$\$', block_math, source, flags=re.S)
source = re.sub(r'(?<!\$)\$(?!\$)([^\n$]+)\$(?!\$)', inline_math, source)
source = re.sub(r'<details class="([^"]+)">', r'<details class="\1" markdown="1">', source)
content = markdown.markdown(source, extensions=['tables', 'fenced_code', 'attr_list', 'md_in_html'])
content = re.sub(r'<div data-math-fragment="(\d+)"></div>', lambda m: fragments[int(m[1])], content)
content = re.sub(r'MATHFRAGMENTTOKEN(\d+)ENDTOKEN', lambda m: fragments[int(m[1])], content)
content = re.sub(r'(<table>.*?</table>)', r'<div class="table-scroll" tabindex="0" aria-label="Scrollable reference table">\1</div>', content, flags=re.S)

chapters = re.findall(r'<h2 id="([^"]+)">(.*?)</h2>', content)
assert len(chapters) == 17, len(chapters)
nav = ''.join(f'<a href="#{identifier}"><span>{title.split(" · ")[0]}</span>{title.split(" · ",1)[-1]}</a>' for identifier,title in chapters)
# Each chapter is a semantic, addressable section. The opening essay stays separate.
parts = re.split(r'(?=<h2 id=")', content)
content = '<header class="book-opening">'+parts[0]+'</header>' + ''.join(
    f'<section class="chapter" aria-labelledby="{chapters[i][0]}">{part}</section>' for i,part in enumerate(parts[1:]))

report = json.loads((HERE / 'audit-report.json').read_text())
style = (HERE / 'style.css').read_text()
script = (HERE / 'labs.js').read_text()
page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="A self-contained course on scheduling, QUBO modelling, algebraic transformations, encodings, Ising models and QAOA, with general proofs and interactive laboratories.">
<title>Scheduling, QUBO & quantum methods — a complete learning guide</title>
<style>{style}</style></head><body>
<a class="skip" href="#book">Skip to the learning guide</a>
<div class="reading-progress" aria-hidden="true"><div id="progress-fill"></div></div>
<header class="topbar"><a class="wordmark" href="#">METHODS / FIELD GUIDE</a><div class="toolbar"><span>Offline edition · 17 October 2026</span><button type="button" id="solutions-toggle" aria-expanded="false">Show all solutions</button><button type="button" id="menu-toggle" aria-expanded="false" aria-controls="contents">Contents</button></div></header>
<aside id="contents" class="contents" aria-label="Table of contents"><p class="nav-title">THE COURSE</p><nav>{nav}</nav><div class="nav-footer"><a href="#reference">Notation & reference ↗</a><p>General rules → derivations → examples → checks</p></div></aside>
<main id="book">{content}<footer class="book-footer"><b>End of the guide.</b><p>Reconstruct a formulation from its rules, explain each transformation, and validate a solution independently. That is the standard to aim for.</p><a href="#orientation">Return to the beginning ↑</a></footer></main>
<script id="audit-data" type="application/json">{json.dumps(report)}</script><script>{script}</script></body></html>'''
(HERE / 'index.html').write_text(page)
print(json.dumps(dict(chapters=len(chapters), numbered_equations=equation_count, math_fragments=len(fragments), words=len((HERE/'guide.md').read_text().split()), html_bytes=len(page.encode()))))
