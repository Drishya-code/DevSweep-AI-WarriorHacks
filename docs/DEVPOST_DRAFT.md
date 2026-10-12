# Devpost submission draft

## Project title

DevSweep AI

## Tagline

Reclaim project storage with explainable, approval-based cleanup and verified recovery.

## Problem

Students and developers often work on laptops with limited storage. Project installs, caches, temporary files, and build outputs accumulate, while manually deleting unfamiliar folders can break a project or remove important data. Beginners need a way to understand what a cleanup candidate is, why it was found, and what will happen before anything is removed.

## Community and intended users

Students and independent developers working on local development projects, especially people using storage-constrained laptops or learning unfamiliar toolchains.

## Proposed solution

DevSweep scans an explicitly selected workspace, finds candidates using deterministic filesystem rules, and presents paths, measured sizes, risk, and explanations. When configured, Nebius Token Factory with NVIDIA Nemotron can add recommendations. The backend independently checks access, candidate identity, protected paths, and risk. The user reviews and approves a plan before execution. The app verifies outcomes and can restore content only when a verified backup was saved.

## Implemented features

- React and TypeScript interface with project scan, cleanup-plan review, execution status, history, and Restore Center.
- FastAPI scanner for a bounded set of common Node.js, Python, and C++ project signals and generated artifact patterns.
- Nebius Token Factory provider configured for NVIDIA Nemotron, with structured recommendations validated against deterministic scanner results.
- Explicit approval, project-bound access checks, protected-file exclusions, candidate re-scan, and fail-closed backup-before-delete.
- SQLite history and SHA-256-verified backup/restore metadata.
- Synthetic demo fixture generator for reproducible local practice.

## Architecture and technical implementation

The React/Vite frontend calls a loopback-only FastAPI service. Deterministic scanning supplies candidate paths, sizes, and scanner risk. The AI provider may recommend actions and explanations, but the server rejects recommendations outside the scan and retains its own authoritative risk, workspace access, approval, and filesystem checks. Before deletion, the server saves content and verifies its manifest. Execution outcomes and verification are recorded in SQLite; Restore Center only exposes verified backups for completed deletions.

## Nebius and NVIDIA integration

The backend uses the OpenAI-compatible Nebius Token Factory API at the configured base URL and defaults to the NVIDIA Nemotron model nvidia/nemotron-3-super-120b-a12b. The application marks a response as live only after successful inference. A mock provider is available when no key is configured for non-destructive development; mock output cannot authorize a cleanup plan. Live inference must be demonstrated with a real configured key and must not be claimed when unavailable.

## Safety and verification

Only scanner-discovered candidates can be planned. Workspace boundaries and path identity are revalidated. Source, configuration, environment, credential, database, and Git paths are protected. DANGEROUS deletion is blocked; CAUTION requires explicit approval. A verified content backup must complete before deletion. Execution results and post-cleanup checks are reported separately from scan-time estimates. Restoration requires approval, a matching project identity, a verified backup, and a destination that does not already exist.

## Demonstrated results

In a local Windows run, the synthetic fixture scanner returned 9 candidates and an estimated 144,989,850 bytes (the app formatted this as 138.3 MB). The API health check succeeded. The provider was the mock provider because no Nebius key was available, so no live inference, cleanup, or restoration was claimed or performed. Replace or supplement these results only with outcomes observed during a live, key-configured demo. The scan estimate is not measured community impact.

## Limitations and future work

The detector covers a bounded set of common patterns, not every development ecosystem. External-folder grant controls are API-only. Live Nebius inference depends on an API key and service availability. Backups are unencrypted, have no automatic retention policy, and do not preserve ownership or platform ACLs. Directory restore can be partial and must be inspected after an error. Future work includes broader detection, integrated grant controls, and a retention policy designed with clear user controls.

## Links and media

- GitHub repository: https://github.com/Drishya-code/DevSweep-AI-WarriorHacks (verify public access after publishing)
- Demo video: add the actual 2–3 minute recording URL after upload.
- Screenshots: add genuine captures from the running app after saving them under docs/images.

## AI-assisted development disclosure

AI assistance was used during development and documentation. Filesystem safety decisions remain enforced by deterministic backend checks; model output is treated as untrusted recommendations.

## WarriorHacks track and deadline checklist

The official event page says the code Hackathon track requires a project with code related to the theme; the Ideathon track does not require a coded project. The event theme is to solve an issue in a community, county, state, or nation. The page requires a GitHub repository, a 2–3 minute demo video, project pictures, and a separate track-selection form for both tracks. The form asks for the project name exactly as entered on Devpost, listed team members, and a track selection. Choose the appropriate track and submit that form manually; do not claim it is complete until verified.

Official links: [WarriorHacks 2.0 overview](https://warriorhacks-2-0.devpost.com/), [track-selection form](https://docs.google.com/forms/d/e/1FAIpQLScYxGmIowiwkZsbmJwWhoc5kPi2_gbJAgeGBAuoMiNPPD_kbA/viewform?usp=dialog), [schedule](https://warriorhacks-2-0.devpost.com/details/dates).

The event page lists the submission deadline as October 13, 2026 at 11:45 p.m. CDT, which corresponds to October 14, 2026 at 10:15 a.m. IST.
