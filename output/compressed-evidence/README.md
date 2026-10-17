# Lossless in-Git evidence assets

These deterministic gzip files preserve the exact large JSON files indexed
in [COMPRESSED_EVIDENCE.json](../COMPRESSED_EVIDENCE.json). Each asset is below
GitHub's 100 MiB blob limit. The original raw paths are ignored locally.

`npm test` restores them automatically through `pretest`; `npm run build` runs
that same prerequisite. Restoration uses Node 20 built-ins and local tracked
files only, without Python, downloads, API calls or credentials.

```sh
node scripts/restore-compressed-evidence.mjs
node scripts/restore-compressed-evidence.mjs --root /absolute/checkout/root
```

Existing raw files must match both size and SHA256 or restoration refuses to
overwrite them. New content is streamed into private staging, verified, atomically
renamed within staging and published with an exclusive same-filesystem hard link
to prevent overwriting a concurrent destination. Only this invocation's partial
files are removed on failure. Unsafe paths and symlinks are rejected.

The existing GitHub release-asset index and restoration script remain separate
and unchanged; these assets require no release upload.

VeloxQ-track assets (`veloxq-*.gz`) cover service results, decoded evaluations
and post-hoc study bundles under `output/catering-methods/veloxq/`. Without
Node, `python3 scripts/restore_veloxq_evidence.py` restores them with the same
SHA256 checks and also unpacks the `*.h5.gz` files stored beside their runs.
