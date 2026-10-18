# Axion Kitchen — submission draft

**Local preparation only. Nothing has been entered or submitted.** The user
requires confirmation before sending the entry. Do not use account details or
commit authors as substitutes for confirmed team identities.

[Official submission form](https://forms.gle/t5YxsRpvUiG1rbdz7) ·
[Expanded Google Form](https://docs.google.com/forms/d/e/1FAIpQLScYtdbyeVzZtlXCKo5Es8bB_G0gmhkayECwmcym78KfO-0gBw/viewform)

The form was inspected on 18 October 2026 without filling any fields. It states
that responses close **18 October 2026 at 15:00 UTC+2**.

## Exact form fields

| Field | Draft value | Status |
|---|---|---|
| Name of the team | **Pending team confirmation** | Required |
| Name of the project | **Axion Kitchen** | Ready for review |
| Team member 1 (first and last name + Discord ID) | **Pending confirmed full name and Discord ID** | Required |
| Team member 2 (first and last name + Discord ID) | **Pending confirmed full name and Discord ID** | Optional field; include actual participating member |
| Team member 3 (first and last name + Discord ID) | **Pending confirmed full name and Discord ID** | Optional field; include actual participating member |
| Team member 4 (first and last name + Discord ID) | **Pending confirmed full name and Discord ID** | Optional field; include actual participating member |
| Team member 5 (first and last name + Discord ID) | Leave blank unless there is a fifth participating member | Optional |
| GitHub repository with project code and required materials | https://github.com/Kolo-Naukowe-Axion/qhackathon26 | Public; anonymous required-file reads verified on 18 October |
| Direct link to the video recording | https://youtu.be/aGu9Mu2BaGg | Correct title and 4:52 duration checked; anonymous oEmbed access succeeds |
| Do you compete for the VeloxQ award? | **Yes** | Matches the team's stated intention; review before submission |

The form has no project-description field. If another organizer surface asks
for one, use the short description in [the handoff](CATERING_FINAL_HANDOFF.md).

## Required checklist — verify before selecting

The form asks for these declarations. The table records verified repository evidence; it does not select boxes in the form.

| Organizer declaration | Evidence / remaining action |
|---|---|
| The code can be run without errors. | Passed all 13 final release stages, including baseline/schema checks, math audits and fresh local sampling. [Receipt](assets/catering-final-check.json). |
| Repository is set to public. | Verified PUBLIC through GitHub; anonymous reads of all required files returned HTTP 200. |
| The repository contains a LICENSE file with a MIT license. | [LICENSE](../LICENSE); retain in the final source tree. |
| README.md has the full instructions on how to run the code. | [README.md](../README.md) includes viewer, Python setup, fresh sampling, release checks and Stage 1 reproduction commands. |
| README.md contains a link to the Demo video. | [README.md](../README.md) links the working 4:52 demo video. Replace/supplement it with the approved YouTube URL when uploaded. |
| The repository contains the Development log. | [DEVELOPMENT_LOG.md](../DEVELOPMENT_LOG.md). |
| The repository contains the Project Design. | [PROJECT_DESIGN.md](../PROJECT_DESIGN.md) and [formal catering problem](CATERING_PROBLEM.md). |
| Schedule files in the output format of Section 14 for both baseline instances. | [schedule_2x2.json](../schedule_2x2.json) and [schedule_3x3.json](../schedule_3x3.json); retain their independent checks. |

## Video and release gate

The current local cut is **4:52**, with 14 chapters, stock male Kokoro
`am_fenrir` narration, captions and matching 4K / 1080p exports in
`output/submission-male-v3/`. Review the latest render and manifests before
uploading. The planned final destination is YouTube; the website will embed
that upload once ready. https://qfactoria.com/video/ is the hosted MP4
review/fallback, not a completed YouTube upload.

Before requesting the user's final confirmation, record:

- YouTube URL: https://youtu.be/aGu9Mu2BaGg; correct title and 4:52 duration observed, anonymous oEmbed available.
- Final source commit: **pending**, record `git rev-parse HEAD` after all changes.
- Public repository check against that commit.
- Final release-check receipt and media/source hashes.
- Exact confirmed team-name and member entries above.

Then show the completed values to the user. **Do not press Submit until the user
confirms.** After an authorized submission, retain the organizer acknowledgment,
submitted URLs, commit and submission time. No receipt exists in this draft.
