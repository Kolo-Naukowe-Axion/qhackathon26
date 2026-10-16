# QHackathon 2026

Team workspace for the QPoland Quantum Hackathon 2026.

## Production deployment

Vercel project: `qfactoria`, personal scope `iwos`. Custom domain: `qfactoria.com`.
The GitHub repository is `Kolo-Naukowe-Axion/qhackathon26`; production follows
`main`. Vercel reads the build settings from `vercel.json`. Keep the project root
at the repository root. Each new push to `main` builds and deploys automatically;
failed tests stop the deployment. Other branches get preview deployments.

Site: https://qfactoria.com (also available at https://qfactoria.vercel.app).
Dashboard: https://vercel.com/iwos/qfactoria.
The Vercel GitHub app has access to this repository only within the Axion organization.

Only the built viewer is public. Repository documents and organizer PDFs are not
included in `dist/`. To roll back, promote a previous ready deployment from the
personal project's Vercel dashboard.

## Run the presentation environment

Requires Node.js 20 or newer. No package installation or API key is needed for the viewer.

```sh
npm run dev
```

Open [the local factory replay](http://127.0.0.1:4173). The server listens only on this machine. Set `PORT` if 4173 is already occupied.

- **Factory:** original pixel-art shop floor with moving parts, processing animations, replay/pause, time scrubbing, speed controls, and part selection.
- **Timeline:** a synchronized Gantt chart; click an operation to jump to it.
- **Evidence:** independent checks for coverage, duration, capacity, and precedence, with explicit result provenance.
- **Present:** a compact presentation layout, with fullscreen where the browser permits it. Space plays/pauses when the page background has focus.
- **Load schedule JSON:** import either the official baseline output format or an `axion-replay.v1` file. Imported metadata is self-reported. Data is processed locally in the browser.
- **Export replay:** download the display wrapper with its source labels; this is separate from the required solver-generated baseline schedule files.

The initial 2×2 and 3×3 schedules are **illustrations copied from the organizer documents**. The 9-hour comparison is a hand-authored illustration. None is evidence of this project's QAOA or VeloxQ execution. Stage 1 remains incomplete until both required methods have actually run and their output schedules pass validation.

## Checks

```sh
npm run check
npm test
npm run build
```

Tests cover schedule feasibility, boundary-time replay state, invalid data, the official JSON adapter, and agreement between the viewer's processing durations and the transcribed official inputs.

The build runs all model tests and syntax checks, then copies only `presentation/`
to `dist/`. No environment variables, backend, database, or third-party runtime
dependencies are required.

## Project material

- `CONTEXT.md`: authoritative requirements, user decisions, known limitations, and current status.
- `instances/`: the two official input datasets transcribed from §14.
- `STAGE1_PLAN.md`: baseline method and evidence plan.
- `DEVELOPMENT_LOG.md`: dated development record, including decisions and rejected approaches.
- `PROJECT_DESIGN.md`: current display model and planned solver interface.
- `docs/PRESENTATION_DESIGN.md`: visual and interaction direction.
- `docs/VELOXQ_IDEAS.md`: proposed VeloxQ formulation and experiment directions.
- `presentation/`: browser-native ES modules, original SVG art, and CSS; no frontend framework or external CDN dependency.

## AI use

OpenAI Codex assisted with extracting and checking organizer requirements, planning, implementation of the presentation environment, original SVG illustration, validation tests, and documentation. The team supplied the objectives, visual references, corrections, and direction. Solver execution and results must be documented separately when they happen. Team members must review the code, understand the formulation and validation, and be able to explain it during the live defense.

Project source is MIT-licensed. The supplied organizer PDFs are reference material from the organizers and are not relicensed by this project.
