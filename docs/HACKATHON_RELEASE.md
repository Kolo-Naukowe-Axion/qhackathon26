# Hackathon snapshot and post-event updates

Axion Kitchen won the QPoland Quantum Hackathon 2026 main prize and shared first
place in the VeloxQ award, as confirmed by the team on 18 October 2026.

[Original video](https://youtu.be/aGu9Mu2BaGg) ·
[Frozen source and media](https://github.com/Kolo-Naukowe-Axion/qhackathon26/releases/tag/hackathon-2026-submission)

The release tag `hackathon-2026-submission` preserves commit
`8ee1bca34f15ee0e900df63857d2dac59b91bfc5` (18 October, 14:53 CEST),
the final repository commit before the 15:00 submission deadline. The form
linked the repository's mutable main branch; this is a reconstructed pre-deadline
snapshot, not a claim that the organizer recorded an immutable commit SHA.
The user confirmed submitting the form. An organizer acknowledgment is not
stored in this repository.

The release also retains the original final video, subtitles and media manifest.
The MP4 is 292 seconds, 3840×2160, with SHA-256:

```
7e9dcbb99d629669fa4a01f33bfdde53ace631bf883250d78479048d2a0475f7
```

`main` includes subsequent live-presentation corrections and post-event packaging:
a new thumbnail, awards text, social previews and a pipeline diagram. These
updates do not change solver outputs, benchmark measurements, baseline schedules
or the submitted video. The video contains the historical full objective;
the current live presentation emphasizes the three distinct priorities because
R equals B in the current fixtures.

## Publicity assets

- [YouTube thumbnail](../presentation/assets/branding/axion-kitchen-winner.jpg):
  1280×720 JPEG, built from the existing kitchen artwork and bundled Axion fonts.
  Rebuild with `python3 scripts/build-publicity-assets.py` (requires Pillow).
- [Pipeline diagram](../presentation/assets/branding/optimization-pipeline.svg):
  local batch enumeration → QUBO → alternative solver paths → independent checks.
- [Website video page](https://qfactoria.com/video/): the new poster frames the
  unchanged original recording. The original poster and manifests remain in place.
