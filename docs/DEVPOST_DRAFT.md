# Devpost submission draft

## Project title

DevSweep AI

## Tagline

Reclaim project storage with explainable cleanup, explicit approval, and verified recovery.

## One-line pitch

DevSweep helps students and developers safely review generated project data before cleanup, then recover deleted items from verified backups.

## Inspiration and problem

Development projects accumulate dependency installs, build output, caches, logs, and temporary data. On a storage-constrained laptop, deleting unfamiliar directories by guesswork can break a project or lose useful work. Beginners need a clear explanation of what a candidate is, why it was found, and what will happen before it is removed.

## What it does

DevSweep scans a user-selected local project or an isolated synthetic demo. Deterministic scanner rules identify candidates and report measured paths, sizes, and risk. When the user configures Nebius Token Factory, NVIDIA Nemotron can recommend actions and explain candidates. The backend independently enforces workspace access, scanner allowlists, risk, protected paths, and approval. Before deletion, each item is copied to a separate backup store and verified. Restore requires approval and refuses to overwrite an existing destination.

## What I implemented

- React, TypeScript, and Vite interface for workspace selection, scan review, plan approval, execution, history, and restore.
- FastAPI scanner for a bounded set of common Node.js, Python, and C++ artifact patterns.
- Optional Nebius Token Factory integration configured for NVIDIA Nemotron. Without live AI, the backend can build a review plan from a fresh deterministic scan; mock output does not select or authorize cleanup items.
- Project-scoped access checks, fresh candidate validation, protected-path rules, and explicit approval gates.
- SHA-256-verified content backups, restore checks, and persistent SQLite operation history.
- Resettable synthetic fixture with real nonzero data to demonstrate review, backup, cleanup, and restore without using a personal project.

## How I built it

I built a React/Vite frontend that talks to a loopback-only FastAPI backend. A deterministic scanner reports candidate paths, measured sizes, and risks. The optional model can recommend only from those candidates; without a successful live analysis, plan contents come directly from a fresh deterministic scan. Server-side code retains authoritative access and safety checks. A plan is review-only until the user explicitly approves execution. The backend verifies a separate content backup before deleting an item, records the outcome, and exposes only verified backups for restore.

## Nebius and NVIDIA

I integrated the OpenAI-compatible Nebius Token Factory API using `nvidia/nemotron-3-super-120b-a12b` by default. The app labels analysis as live only after a successful real provider request. A configured key alone is not proof of live inference. Mock mode is clearly labeled and mock output is not used to select cleanup plan contents.

## Safety and limitations

Cleanup targets must be scanner-discovered, within the authorized project, and pass fresh server-side validation. Source, Git history, secrets, environment files, and protected configuration are excluded. DANGEROUS candidates are blocked; CAUTION candidates require review and approval. The backend verifies backups before deleting and will not overwrite files during restore.

The detector covers a bounded list of common artifact names and ecosystems. External-folder grant controls are currently API-only. Backups are not encrypted and have no automatic retention policy; they do not preserve ownership or platform ACLs. Verification checks filesystem and protected-file state and does not automatically run the project's build or test suite. Large folders can take minutes to back up and verify.

## Demonstrated results and evidence

A local Windows scan of the reset synthetic fixture found nine nonempty candidate groups totaling 144,989,850 bytes (about 138.3 MiB). One real Nebius analysis request succeeded and returned recommendations; that verifies a live request occurred during development, not that every run or judge's environment will have provider access.

In a subsequent approved local demo execution, the backend recorded seven of seven selected items deleted with zero failed or unknown items, and about 117.4 MB processed. It recorded verified backups for those deletions. A later approved restore of the 79,962,748-byte synthetic `node_modules` backup completed; the restored directory contained 3,106 files and did not overwrite existing files. The operation history did not record a post-cleanup verification result for that particular execution, so this draft does not claim that separate verification passed for it. Source and package files were present after restore.

**Gallery:** genuine application screenshots and a small number of designed graphics are included in [`docs/submission/devpost-gallery/`](submission/devpost-gallery/). The [gallery manifest](submission/devpost-gallery/gallery-manifest.md) distinguishes them and records the evidence each supports. **YouTube demo:** [Watch DevSweep AI](https://youtu.be/9oGs6lo1hrc) (URL supplied by the project owner; playback was not independently verified in this environment). The production notes describe the source clips in this repository and why no finished edited MP4 is claimed here.

The end-to-end counts and SHA-256 values above are historical local synthetic-demo evidence; see the dated [verification report](submission/demo/verification-report.md). They are not a claim that this repository update has just repeated that destructive workflow.

## What we learned

Keep model recommendations separate from filesystem authority. A plan can become stale after a scan, so execution must recheck it. Backups improve recoverability but add noticeable time for directories with many files; visible progress and honest status matter. Local verification is also narrower than running the project's own tests.

## Future work

Broaden well-tested artifact detection, add user-facing controls for temporary external-folder grants, design transparent backup retention controls, and improve post-cleanup project checks without running untrusted commands automatically.

## Links

- GitHub: https://github.com/Drishya-code/DevSweep-AI-WarriorHacks
- Local demo guide: [docs/DEMO.md](DEMO.md)
- Demo scripts and verification notes: [docs/submission/demo/](submission/demo/)
- YouTube demo: [Watch DevSweep AI](https://youtu.be/9oGs6lo1hrc)
- Genuine application screenshot gallery: [gallery index](submission/devpost-gallery/README.md)
- Judge quick guide: [Markdown](submission/DevSweep-AI-Judges-Quick-Guide.md) · [PDF](submission/DevSweep-AI-Judges-Quick-Guide.pdf)

## AI-assisted development disclosure

AI assistance was used for implementation and documentation. Model output is treated as untrusted advice; deterministic backend checks and explicit user approval govern filesystem changes.

## Submission context

I submitted this project for WarriorHacks 2.0. Repository improvements made after that submission do not retroactively change the submitted Devpost entry or imply a judging outcome. The YouTube URL above was supplied for this repository update; playback was not independently verified here.

Official event references: [WarriorHacks 2.0](https://warriorhacks-2-0.devpost.com/), [track-selection form](https://docs.google.com/forms/d/e/1FAIpQLScYxGmIowiwkZsbmJwWhoc5kPi2_gbJAgeGBAuoMiNPPD_kbA/viewform?usp=dialog), [schedule](https://warriorhacks-2-0.devpost.com/details/dates).
