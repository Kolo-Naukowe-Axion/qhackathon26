# Stage2 written walkthrough

`index.html` is the readable document generated from the canonical source, `../STAGE2_PROBLEM_WALKTHROUGH.md`. It follows the prose-first reading style of `../learning-methods/index.html`: substantial text, addressable sections, a fixed contents sidebar, scrollable tables/code and a dedicated print layout. The original learning-methods files are untouched.

Open `index.html` locally in a modern browser. Its typography, navigation and progress indicator are embedded, with no CDN, network request or runtime package. Repository-relative evidence links work while the file remains in this folder. The main written source remains the Markdown; edit that source and rebuild rather than editing generated HTML. `build-report.json` retains exact source/style/builder/HTML hashes, chapter titles and local-link mappings.

Build:

```sh
node docs/stage2-problem/build.mjs
python3 docs/stage2-problem/audit.py
```

The build-only parser is `marked17.0.5`, available in the Codex bundled Node dependencies. Another installation can be selected using `MARKED_MODULE=/absolute/path/to/marked/lib/marked.esm.js`. The reader does not need this package. The renderer supports standard Markdown tables, fenced code, lists, inline code, links and GitHub callouts; formulas are readable source text/code, not remotely rendered math. Links relative to the Markdown’s `docs/` directory are rebased for the HTML subdirectory and verified before writing. No solver, engine, simulation, circuit or experiment is imported or executed.

The render audit checks exact provenance, unique headings, table wrappers, local links/anchors, offline assets and responsive/print styles. It does not independently validate the scientific claims; the root agent owns the canonical text and fact checks. Browser review is recorded separately after the document has been rendered.
