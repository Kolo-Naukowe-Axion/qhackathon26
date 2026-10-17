# Full offline final-evidence archive

`output/stage2-search/final-full-evidence-v2.tar.gz` is a private local evidence
archive, not a new selected policy, commit, deployment or publication.

- Compressed size:116,815,605 bytes; uncompressed payload:1,459,960,552 bytes.
- Archive SHA256:`185fb11fe991b39e5e1494e377d14501cfb4ce986e395059741139f16152977c`.
- Descriptor:`final-full-evidence-v2.tar.gz.descriptor.json` beside the archive.
- Manifest SHA256:`ad211258744056981d3b27cc7e311b9869f41a8a5cb5feba283e1f3ccae9eab0`.

The3,005 payload files retain the exact40-file current runtime at repository
root, both original current/legacy40-file snapshots and archives, the exact
global bundle, all10 untrimmed final cohorts,23,552 rows,592 predeclared retained
traces, the complete original41-contrast report, original absolute index, a new
relative reproduction index, independent audit reports and primary certificates.
Three posthoc diagnostic traces remain separately labeled. The compact TRAIN
neighborhood supplement remains development evidence, not additional final
samples. The legacy runtime is retained for provenance, not substituted with the
current implementation and described as a policy rerun.

The manifest hashes every payload. Its own bytes and the compressed archive are
pinned by the external descriptor, avoiding a circular self-checksum. These
checks detect corruption and are not an external signature or proof of authorship.
Files were streamed directly from originals; no initial1.46GB staging copy was
needed. Only reporting/package helpers outside the sealed40 sources were added.

After extraction, use Python3.12+ and the included NumPy-only requirements.
Installing NumPy needs a package index/cache; all reproduction after that is
offline. Run from the extracted root:

```sh
python -m pip install -r requirements-final-evidence.txt
python -m stage2.full_evidence_archive verify --root . --descriptor /path/to/final-full-evidence-v2.tar.gz.descriptor.json
python -m stage2.final_report --index output/stage2-search/final-full-evidence-index-relative.json --output reproduced-final-report --bootstrap 2000
python -m stage2.full_evidence_archive compare-report --output reproduced-final-report
python -m stage2.full_evidence_archive audit-all --output reproduced-trace-audits
```

The audit command rechecks all592 predeclared retained traces against fresh
numerical instances without running a factory or solver. Outputs must be new
paths. Original remote/absolute strings are opaque provenance; actual inputs use
the relative index and preserved repository layout.

Verification used a fresh `/private/tmp` extraction and isolated Python3.14.6
environment with NumPy2.5.4 and pip only. All3,005 payload files and the manifest
seal passed byte checks. Full aggregation reconstructed74 groups/23,552 rows with
zero invalid entries and all41 contrasts at2,000 bootstrap replicates in102.252s.
All numeric/statistical payloads, interval limits and reporting source hashes
match exactly; only actual local evidence paths and top-level aggregation elapsed
time are excluded. A complete frontier cohort first independently passed72 fresh
physical/identity replay checks in19.994s. A separate fresh version2 extraction
then ran the supplied `audit-all` command over all10 cohorts and all592
predeclared retained traces. Every fresh numerical-instance, physical/identity,
checkpoint/source/protocol normalization and cached-summary reconstruction gate
passes using only NumPy and pip; torch, SciPy and OR-Tools are absent. This
additionally verifies the learned and legacy checkpoint portability. None of
these commands runs a factory or solver.

Receipts beside the archive are
`final-full-evidence-v2-reproduction-receipt.json` and
`final-full-evidence-v2-stream-verification.json`; the separate full portability
receipt is `final-full-evidence-v2-all-trace-audits-receipt.json`, with all10
per-cohort outputs preserved in the corresponding directory. Version1 remains unchanged:
its README incorrectly said Python3.11+ although pinned NumPy requires3.12+.
Version2 changes only that README/command and the packaging helper. All3,003
scientific payload files, frozen sources, outcomes, intervals and source archives
are byte-identical to version1, so the exact scientific reproduction receipt
applies to both. The separate version1 erratum remains preserved.
