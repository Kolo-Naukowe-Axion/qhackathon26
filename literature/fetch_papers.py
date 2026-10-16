#!/usr/bin/env python3
"""Download the curated public papers and record PDF integrity/provenance.

Requires curl, pdfinfo and pdftotext. Existing valid PDFs are reused.
Unavailable papers stay in the index with their canonical source links.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent


def inspect_pdf(path, title):
    if path.read_bytes()[:5] != b"%PDF-":
        raise ValueError("response is not a PDF")
    info = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True, check=True)
    pages = int(re.search(r"^Pages:\s+(\d+)", info.stdout, re.M).group(1))
    extracted = subprocess.run(
        ["pdftotext", "-f", "1", "-l", "2", str(path), "-"],
        capture_output=True, text=True, check=True,
    ).stdout.lower()
    words = set(re.findall(r"[a-z]{4,}", title.lower()))
    matched = sum(word in extracted for word in words)
    if not extracted.strip() or matched < max(2, len(words) // 2):
        raise ValueError("first-page text does not match expected paper title")
    return {"pages": pages, "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def fetch(source):
    result = dict(source)
    destination = ROOT / "papers" / (source["id"] + ".pdf")
    if destination.exists():
        result.update(inspect_pdf(destination, source["title"]))
        result.update(status="downloaded", file=str(destination.relative_to(ROOT)))
        return result
    failures = []
    for url in source["pdf_urls"]:
        try:
            with tempfile.TemporaryDirectory() as temp:
                candidate = Path(temp) / "paper.pdf"
                transfer = subprocess.run(
                    ["curl", "--fail", "--location", "--silent", "--show-error",
                     "--connect-timeout", "15", "--max-time", "75", "--output", str(candidate), url],
                    capture_output=True, text=True,
                )
                if transfer.returncode:
                    raise ValueError(transfer.stderr.strip())
                details = inspect_pdf(candidate, source["title"])
                destination.write_bytes(candidate.read_bytes())
                result.update(details)
                result.update(status="downloaded", file=str(destination.relative_to(ROOT)), downloaded_from=url)
                print(f"Downloaded {source['id']}: {details['pages']} pages", flush=True)
                return result
        except (ValueError, OSError, subprocess.CalledProcessError) as error:
            failures.append({"url": url, "reason": str(error)[:300]})
    result.update(status="link_only", file=None, download_failures=failures)
    if not source["pdf_urls"]:
        result["availability_note"] = "Publisher full text requires subscription; canonical link retained."
    print(f"Link only: {source['id']}", flush=True)
    return result


def main():
    sources = json.loads((ROOT / "sources.json").read_text())["sources"]
    (ROOT / "papers").mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as executor:
        records = list(executor.map(fetch, sources))
    manifest = {"retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                "validation": "PDF signature, pdfinfo parsing and expected-title text on first two pages",
                "sources": records}
    (ROOT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    collections = [
        ("stage2", "Stage 2 extension literature", "STAGE2_LITERATURE.md", "Annotated Stage 2 guide"),
        ("baseline-methods", "Baseline formulation and quantum-method literature", "BASELINE_METHODS_REVIEW.md", "Baseline and methods review"),
    ]
    lines = ["# Literature collection", "",
             " · ".join(f"[{label}]({guide})" for _, _, guide, label in collections)
             + " · [Reading list (CSV)](reading_list.csv) · [Source catalog](sources.json) · [Download manifest](manifest.json)", "",
             "PDFs are public publisher/author manuscripts or arXiv preprints. Their original copyright and license notices apply; the repository MIT license does not relicense third-party papers.",
             "Existing contributions, including `papers/Learning to Optimize.pdf`, are retained separately.", ""]
    for key, heading, guide, label in collections:
        subset = [r for r in records if r.get("collection", "stage2") == key]
        got = sum(r["status"] == "downloaded" for r in subset)
        lines.extend([f"## {heading}", "", f"Guide: [{label}]({guide}). {len(subset)} references; {got} with local PDFs.", "",
                      "| Guide entry | Paper | Local copy |", "| --- | --- | --- |"])
        for record in subset:
            local = f"[PDF]({record['file']}) ({record['pages']} pages)" if record["file"] else "Source link; PDF unavailable"
            lines.append(f"| {record['guide_entry']} | [{record['title']}]({record['source_url']}) | {local} |")
        lines.append("")
    lines.extend(["To retry missing downloads: `python3 literature/fetch_papers.py` (requires curl and Poppler).",
                  "Checksums, source URLs, retrieval failures and downloaded versions are recorded in the manifest.",
                  "Downloaded availability does not mean a paper was fully reviewed or its experiments reproduced; see the evidence notes in each guide.", ""])
    (ROOT / "README.md").write_text("\n".join(lines))
    downloaded = sum(record["status"] == "downloaded" for record in records)
    print(f"Complete: {downloaded} PDFs, {len(records) - downloaded} link-only references", flush=True)


if __name__ == "__main__":
    main()
