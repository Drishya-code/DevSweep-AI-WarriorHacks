# DevSweep AI demo narration

**Target cut:** 2:45
**Voice:** not recorded or synthesized; this is a script-only narration deliverable.
**Music:** none; keep the interface audio-free and narration clear.

## 0:00–0:20 — Personal hook

As a B.Tech Computer Science student, I spend a lot of time building projects. I’ve noticed the same thing among friends and fellow students: projects leave behind dependencies, build outputs, caches, and temporary files. Deleting the wrong thing can break a working project.

## 0:20–0:38 — DevSweep AI

I built DevSweep AI to make that decision easier to review. Its guiding idea is simple: Clean. Keep. Restore. It identifies cleanup candidates, protects project files, and keeps a verified backup before an approved deletion.

## 0:38–1:00 — Workspace and scan

I’m choosing the isolated synthetic demo workspace. This folder contains generated test data, not my application source. The scan found nine candidates with about 138 megabytes of candidate data. That number is an estimate of listed items, not storage already recovered.

## 1:00–1:25 — AI analysis

For this run, the interface reports analysis by Nebius using NVIDIA Nemotron, and the live request succeeded. The scanner supplies the candidate paths and measurements; the model adds recommendations. The backend still enforces the safety rules. Source and configuration are not cleanup candidates.

## 1:25–1:52 — Review and approval

I’m reviewing the proposed plan and choosing just one small synthetic file: temp-artifact dot T-M-P, classified SAFE and measured at 96 kilobytes. The plan shows exactly what will be removed. I review the path and risk, then explicitly approve execution in the application.

## 1:52–2:15 — Cleanup and verification

The application reports that one item was deleted and zero failed. Its post-cleanup checks passed, including checks that the source directory and package manifest remain present. The Git check was skipped because this synthetic fixture is not itself a Git repository.

## 2:15–2:32 — Restore

Before deletion, DevSweep created a backup that passed SHA-256 verification. I reviewed the backup and confirmed the restore. The application reports a completed restore without overwriting an existing file, and the restored test artifact matches its original hash.

## 2:32–2:45 — Close

I built DevSweep AI to help developers clean with confidence while keeping a recovery path. Clean. Keep. Restore. The project is on GitHub at Drishya-code slash DevSweep-AI.
