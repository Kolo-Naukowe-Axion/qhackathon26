# Qfactoria release log

- Artifact: static factory replay web app, version 0.1.0.
- Target: Vercel project `qfactoria`, personal scope `iwos` (verified owner, Pro).
- Requested domain: `qfactoria.com`, registered with Cloudflare.
- User authorization: 2026-10-16 request to deploy publicly on personal Vercel and continuously deploy GitHub main. This authorizes production deployment and its required repository/configuration changes.

## Preflight

- PASS: source and illustrative datasets are present; no blocking placeholders in viewer code.
- PASS: all 10 model tests and JavaScript syntax checks.
- PASS: production build copies only viewer assets to `dist/`.
- PASS: no third-party dependencies or production environment variables required; no hardcoded credentials found in viewer/build inputs.
- PASS: local browser smoke check of factory, timeline, evidence, schedule switching, and playback. No browser errors reported.
- PASS: README, changelog, sitemap, robots.txt, custom 404, CSP and response headers added.
- PASS: version remains 0.1.0 for the first release.
- WARNING: Lighthouse performance/accessibility scores have not been measured.
- No analytics configured: not required for this static hackathon viewer.

## Deployment

- Personal Vercel project created and local checkout linked.
- First production deployment READY: `dpl_8QQqowcopnTnjkoY4pMGPpjgbxJs`, https://qfactoria.vercel.app (2026-10-16 18:59 Europe/Warsaw). Vercel build passed all 10 tests.
- Approved source/configuration commit pushed to main: `cb04402`. Organizer PDFs and research notes were excluded.
- Domain verified. Cloudflare apex CNAME points to Vercel's preferred project-specific `8b56333f7ea23e10.vercel-dns-016.com`, DNS only, TTL Auto. Vercel reports Valid Configuration. (Replaced the working legacy A record initially suggested by the CLI.)
- HTTPS: Vercel issued `cert_9CkWdpcxYgFpjiDjMsJ6xInA` for qfactoria.com, with automatic renewal.
- With action-time user approval, installed the official Vercel GitHub app for only `Kolo-Naukowe-Axion/qhackathon26` within the Axion organization.
- Git integration connected successfully; production branch verified as `main`.
- Pushed documentation commit `a98a54f` after connecting Git. This automatically created production deployment `dpl_84kyaF5kKjGqLyKRHJeUFms9vnEw`, READY, and GitHub's Vercel status is success. No scheduled polling is needed.

## 2026-10-16 — Factory/manual and complete local baseline release

- User explicitly requests all new work committed and pushed to main, with production deployment, after updating documentation. This is the publishing approval; no additional confirmation is needed.
- Target reverified as personal `iwos/qfactoria`, project `prj_Bqj5S6AT4MsAsa2nT7uAxrAAg2l2`, domain qfactoria.com, repository Kolo-Naukowe-Axion/qhackathon26.
- Documentation updated before staging: README, changelog, Project Design, context, presentation design, compliance/readiness and the public field manual’s selected results. Version remains 0.1.0 for the same-day private app release.
- PASS: 16 Node tests, syntax checks and static production build. PASS: 19 core Python tests; 2 optional IQM compilation tests pass in the dedicated environment.
- PASS: selected 4 h / 8 h outputs verify independently, including reconstruction of the saved quantum expectations/counts.
- PASS: custom secret scan of 769 candidate files/archive members, including decompressed experiments, found no credential matches. A staged gitleaks scan follows before commit.
- WARN: Lighthouse numerical performance/accessibility scores are not measured. Browser checks cover the core interactions and phone layout. No third-party frontend dependencies, production secrets or server-side runtime are needed.
- GitHub main includes two newer literature/tutorial commits to preserve during integration. The hosted build excludes repository documents, solver evidence and PDFs.
- External solver holds remain intact; this release makes no VeloxQ/ODRA5 call.

- PASS: staged gitleaks scan inspected ~225.61 MB of changes and found no leaks. Generated circuit ASCII diagrams retain their original trailing spaces; source/docs whitespace checks pass.
- PASS: newer tutorial/literature commits integrated, append conflicts resolved by preserving both contributions, imported historical-result descriptions reconciled with the current selected evidence.
- Repository visibility verified PRIVATE, default main. No visibility change is authorized or performed; public-source competition eligibility remains a separate documented condition.

- User selected: deploy the completed release now and leave the ten visual variants in progress.
- A further tutorial commit `e277c37` arrived before push. Integrated it in an isolated Git worktree, preserving its expanded derivation and the current-evidence notes; the in-progress variant workspace stays untouched.
