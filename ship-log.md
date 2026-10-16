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
