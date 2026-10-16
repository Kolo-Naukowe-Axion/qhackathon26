# Presentation design

## Direction

Visual thesis: an original pixel-art workshop in a quiet rural landscape, with the legibility of a scheduling tool. Factorio and Stardew Valley are directional references for visible production, machinery, and warm pixel environments; no game assets are copied.

Content plan: orient viewers to the instance and source, replay the factory, inspect an individual part, inspect the time schedule, and verify the result. The factory is the dominant visual; evidence stays one tab away.

Interaction thesis:

- Time drives the scene, machine progress, part states, finished count, and Gantt cursor together.
- Select a part to connect its route to all its operations; selecting a Gantt operation seeks to its start.
- Belts and machine mechanisms animate only during playback. No autoplay. Respect reduced-motion preferences for decorative animation.

## Meaning and limitations

- Part colors and text ids are consistent across scene, timeline, and controls. Color is never the only identifier.
- Processing occupies half-open intervals `[start,end)`, matching the feasibility checker. A part can switch machines exactly at the completion boundary.
- Waiting, processing, complete, and missing/unscheduled states are distinct.
- Travel animation and scenery are explanatory art. They add no transport time to the mathematical schedule.
- Each imported or illustrative record shows its provenance. Feasibility checking does not authenticate remote execution or establish global optimality.
- Initial illustrations reproduce the organizers' problem, but do not count as the team's solver runs.
- The first scene supports two or three machines and up to twelve parts following the displayed common route. More machines, outages, setup times, and partial operations need explicit model/view extensions.

## Presentation strategy

Use the factory to explain the problem first, then the linked timeline to explain the schedule, then evidence to establish correctness and source. For real solver work, connect each visual to an actual saved run and the classical reference on the same model.

After the baseline works, add Stage 2 overlays only for selected, implemented constraints. The official challenge explicitly requires a substantive extension; presentation alone cannot replace it.

## Visual cleanup — 2026-10-16

- User requested a series of visual passes to remove generic promotional text and focus on the factory. Removed the introductory heading, question, stage eyebrow, repeated scene instructions, and footer slogan. Successful checks no longer repeat themselves in explanatory paragraphs.
- Replaced the provisional asterisk/wordmark treatment with the actual Axion logo from `axion2.0`, with locally bundled Space Grotesk and Manrope matching that source project's branding.
- Moved source/type information to a compact strip above the factory; detailed method/provenance remains in Validation. Illustration/solver distinctions remain explicit.
- Replaced full pastel Gantt fills with neutral bars and small job-color markers. Selection uses a dark fill; unselected labels remain readable without low-opacity fading or heavy outlines.
- Removed reserved empty scene/intro space and reduced the interface to tabs, instance selection, playback, parts, metrics, and the schedule.
- The named pstack `/unslop` workflow was not installed or found in the session's skills/plugins. The user's concrete cleanup directions were applied directly.

## Factory-world redesign and field manual — 2026-10-16

- The live pixel factory now forms the full page landscape rather than an embedded illustration. Grass, paths, trees and stations share the same palette as timber-framed controls and parchment records.
- The current HUD uses a typographic Axion emblem and locally bundled Manrope; earlier imported-logo/Space Grotesk notes above describe the previous design pass.
- Top navigation exposes Factory world, Control desk and Stage 1 guide. The control desk contains Timeline and Validation; switching views preserves clock and selected part. World signposts also open those menus.
- `/problem-explanation` uses a parchment field manual with six chapter links, previous/next controls and a return-to-factory link. The mobile chapter list scrolls horizontally.
- Interactive diagrams compute permutation schedules, exactly-one penalties, all four compact A bit choices, factorial order counts and statevector memory. The explanatory text includes proof assumptions, complexity notation and the distinction between sampled feasibility and exact optimality.
- Solver summaries now match `output/stage1-selected.json`; earlier p=5/2,000-sweep runs remain archived. Both remote solver holds remain in effect.
- Checked desktop and 390-pixel phone layouts, keyboard-accessible controls, navigation and constraint feedback. The production build has 16 Node tests plus syntax checks.
