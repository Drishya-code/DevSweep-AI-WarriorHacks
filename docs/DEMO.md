# Reproducible synthetic demo

Published recording: [Watch DevSweep AI on YouTube](https://youtu.be/9oGs6lo1hrc) (link supplied by the project owner).

This walkthrough uses only the isolated `demo-project` fixture. Never select the repository root or a personal project for a destructive demo. A fresh deterministic scan is enough to prepare a review-only plan; live Nebius analysis is optional. Cleanup still requires explicit in-app approval and all backend validation and backup checks.

## Prepare on Windows

From the repository root, install dependencies and create the fixture only if it is missing:

```powershell
if (-not (Test-Path .\backend\.venv\Scripts\python.exe)) { py -m venv .\backend\.venv }
if (-not (Test-Path .\frontend\node_modules\vite\bin\vite.js)) { Push-Location .\frontend; npm.cmd ci; Pop-Location }
if (-not (Test-Path .\demo-project)) { .\backend\.venv\Scripts\python.exe .\generate_demo.py }
```

No `.env` file is required. For the one-command launcher, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` and then `./Start-DevSweep.ps1`. This starts no-key mode by default. For live inference, add your own key to the ignored root `.env`, set `DEVSWEEP_DEMO_MODE=false`, and run `./Start-DevSweep.ps1 -LiveAI`. Keep `.env` private; never show a key in a recording, screenshot, terminal, or frontend setting. A configured provider is not proof of successful inference. Say “live Nebius analysis” only after the real request succeeds.

### Backend terminal

Open a new PowerShell window at the repo root:

```powershell
Set-Location 'C:\path\to\DevSweep-AI-WarriorHacks'
$env:DEVSWEEP_WORKSPACE_ROOT = (Resolve-Path .).Path
$env:DEVSWEEP_DEMO_MODE = 'true'
$env:NEBIUS_API_KEY = ''
Set-Location .\backend
..\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Frontend terminal

Open another PowerShell window:

```powershell
Set-Location 'C:\path\to\DevSweep-AI-WarriorHacks\frontend'
npm.cmd run dev -- --host 127.0.0.1
```

Open the local URL Vite prints, normally `http://127.0.0.1:5173`. Use `npm.cmd` in PowerShell if the execution policy blocks `npm.ps1`. If port 8000 is busy, check whether a backend is already running before starting another.

## Demo flow

1. Choose **Try Safe Demo**. Confirm the selected path ends in `demo-project`.
2. Show `demo-project/src` and `demo-project/package.json` as protected examples.
3. Scan the fixture. A reset currently creates nine synthetic candidate groups totaling 144,989,850 bytes (about 138.3 MiB / 144.99 MB decimal). These are current size estimates, not savings already achieved. Candidate totals can change if scanner patterns change.
4. Optionally run AI analysis. Point out the provider/model only if the app confirms a successful live request. Without credentials, skip AI and review the deterministic scan; mock/demo output is labeled and is not used to select plan contents.
5. Review each path and risk. SAFE candidates include generated outputs such as `dist` (about 14.4 MB), `coverage` (about 2.8 MB), and `temp-artifact.tmp` (96 KB); `node_modules` is about 76.3 MB. The larger `logs`, `cache`, and `review-me` candidates are CAUTION. Include only items you have reviewed. The backend refreshes scanner results and supplies authoritative risk and measured sizes to a plan.
6. Create the plan and inspect its exact items and risks. Explicitly approve only after review. The backend backs up and verifies each item before deleting it. Large folders with thousands of files may take several minutes; the app displays current item progress.
7. Show execution and verification separately. Verification is not a substitute for a project build/test, and an integrity-check pass alone does not mean a file was deleted.
8. In Restore Center, inspect the verified backup for an item that the execution record says was deleted. Approve restore. Existing files are never overwritten; if the destination already exists, restore safely refuses.
9. Confirm the restored artifact exists and that `src` and `package.json` remain present. Claim success only when the app and filesystem confirm it.

## Reset between takes

Close or leave any existing plan; it refers to the prior scan. From the repository root:

```powershell
.\backend\.venv\Scripts\python.exe .\generate_demo.py
```

Then return to the app and choose **Try Safe Demo** to create a fresh scan. Reset only targets the dedicated synthetic `demo-project` directory after link/junction safety checks. It does not clear SQLite history or the separate backup store. The app's **Reset Demo Sandbox** action runs the same generator. Do not reset while a cleanup or restore operation is still running.

## Recording guide (about 2 minutes 40 seconds)

- **0:00–0:20:** Introduce the storage problem and risk of deleting by guesswork.
- **0:20–0:45:** Show the synthetic workspace and protected source/configuration examples.
- **0:45–1:20:** Scan; review measured candidate sizes, descriptions, and risk. Explain which state is scanner output and which is AI recommendation.
- **1:20–1:50:** Review the exact plan, approve a carefully chosen candidate, execute, and show the real result. Keep the capture running while a large verified backup completes.
- **1:50–2:15:** Show verification. Review and restore a verified backup only if the run completed and the destination is absent.
- **2:15–2:40:** Summarize model role, backend safety gates, and limitations. Clearly label any provider failure or skipped step.

## Screenshots and video

Genuine application screenshots and designed project graphics are in [the Devpost gallery](submission/devpost-gallery/README.md); [`gallery-manifest.md`](submission/devpost-gallery/gallery-manifest.md) states which is which. The screenshots demonstrate an earlier synthetic workflow, including successful live analysis and execution. They predate the latest no-key plan support. Capture a new real scan and plan screen if you want the recording to show no-key mode.

Do not expose API keys, private paths, or personal information. Do not make a missing step look successful through edits. Record the actual application for 2–3 minutes, review playback/audio/readability, and link the uploaded recording only after checking the exact public URL. No edited MP4 is currently present in the repository; the production notes describe the recording limitations and supplied source clips.
