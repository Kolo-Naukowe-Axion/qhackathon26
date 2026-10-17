# Start here

Open **index.html** in a modern browser. It is the complete, portable learning guide: no server, internet connection, installation or account is needed. Keep or share that one file to preserve the equations and interactive labs.

Read chapters 01–06 first. Chapter 03 contains the algebra transformation workshop; 07 generalises encodings; 08 develops objectives and extensions; 09–12 connect the model to Ising, quantum mechanics, QAOA and solver mechanisms. Chapter 13 works through the supplied instance, 14 contains sixteen exercises with worked solutions, and 15 is a reference sheet.

Use **Show all solutions** when reviewing, or open answers individually while studying. On a narrow screen use **Contents** for navigation. Wide equations and tables scroll inside their own regions. Ordinary browser printing uses a dedicated layout and expands the answers; no PDF file is bundled.

## Reproducibility

The mathematical audit uses the standard library and imports the existing repository builder:

```sh
python3 docs/learning-methods/audit.py
```

To edit and rebuild, change `guide.md`, `style.css`, or `labs.js`. In a Python environment of your choice:

```sh
python3 -m pip install -r docs/learning-methods/requirements-build.txt
python3 docs/learning-methods/build.py
```

Build packages are not needed by the reader. The audit report and quality record document verification and its limits. The source tutorial and the repository's existing presentation files were preserved.
