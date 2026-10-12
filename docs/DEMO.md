# Reproducible demo

This demo uses only the synthetic project in demo-project. Do not select the repository root or a real personal project for destructive operations.

## Prepare and run (Windows PowerShell)

Run this once from the repository root to prepare the isolated fixture and backend environment:

```powershell
python .\generate_demo.py
python -m venv .\backend\.venv
.\backend\.venv\Scripts\python.exe -m pip install -r .\backend\requirements.txt
Copy-Item .\.env.example .\.env
```

Edit the root `.env` locally. Set `DEVSWEEP_WORKSPACE_ROOT` to the full path of this checkout and add `NEBIUS_API_KEY` only if live inference is intended. Keep `.env` private; never put a key in a frontend variable, terminal capture, screenshot, or video.

Start the backend in Terminal 1 from the repository root:

```powershell
$env:DEVSWEEP_WORKSPACE_ROOT = (Resolve-Path .).Path
Push-Location .\backend
.\.venv\Scripts\python.exe -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Start the frontend in Terminal 2:

```powershell
Set-Location .\frontend
npm ci
npm run dev -- --host 127.0.0.1
```

Open the URL printed by Vite (normally http://127.0.0.1:5173) and check the provider indicator. If it says `mock`, the scan and interface can be explored, but the backend correctly refuses to create an executable cleanup plan. Do not describe mock output as live AI. The synthetic fixture is separate from the app source and is generated only by `python .\generate_demo.py` from the repository root.

## Walkthrough

1. Show demo-project/src and package.json before cleanup. These are the protected source and configuration examples.
2. In Scan Workspace, scan demo-project. Explain that listed byte totals are current-size estimates, not savings already achieved.
3. Run AI analysis. Point out the provider/model and whether the result came from live Nebius inference. Scanner paths and sizes remain deterministic; the model provides recommendations and explanations.
4. Review temp-artifact.tmp as the disposable temporary example, generated directories such as dist or .vite as regenerable outputs, and review-me as an uncertain directory that needs careful review. Select only the item(s) you intend to remove. The caution item requires explicit approval.
5. Generate the plan. Show the exact path, risk, reason, size, and application-side safety checks. Check the approval box only after reviewing the plan, then execute.
6. Show the execution outcome and post-cleanup verification. Explain that the reported freed bytes come from the operation result.
7. Open Restore Center, inspect a verified backup, and restore the selected temporary artifact if the backend reports a completed backup. The restore requires a second approval and will not overwrite an existing file.
8. Rescan or inspect the demo project to show the restored temporary file and that src and package.json remain present. Do not say restoration succeeded unless the UI reports it.

If an operation fails, show the actual error and do not edit the UI state or substitute a simulated result.

## Reset between runs

Close the active plan, then run `python generate_demo.py` from the repository root. This recreates generated demo contents with fixed sizes and repeatable harmless bytes. It does not reset application history or remove backups; the SQLite history and backup directory are separate from the demo fixture. Review and manage those records through the app and local files as needed.

The optional POST /api/scan/demo/reset route runs the same generator. Use it only when you intentionally want to reset the demo fixture.

## Recording script (about 2 minutes 40 seconds)

- 0:00–0:20 — “Students and developers can run short on laptop storage as project installs and build outputs accumulate. Deleting files by guesswork can break a project.”
- 0:20–0:45 — Show the synthetic demo workspace and start the scan. “This fixture is local and synthetic. The source and package manifest are protected.”
- 0:45–1:20 — Review candidate paths, sizes, explanations, and risks. Distinguish deterministic scanner findings from the configured AI provider. Call the storage number an estimate.
- 1:20–1:50 — Review the exact plan, approve the chosen item, and execute cleanup. Show the actual outcome.
- 1:50–2:15 — Show verification and, if it completed, inspect and restore the verified backup. Point out that restore refuses to overwrite.
- 2:15–2:40 — Explain that Nebius Token Factory with NVIDIA Nemotron can recommend actions, while deterministic backend checks and user approval govern execution. State the bounded detector and backup limitations.

## Genuine screenshots and video

Use Windows Snipping Tool (`Win+Shift+S`) on the running app and save genuine captures under `docs/images` with these names:

1. `01-scan-findings.png` — the completed scan and candidate list, with the provider label visible.
2. `02-reviewed-plan.png` — the exact selected paths, risks, and approval controls before execution.
3. `03-verification-restore.png` — the actual post-cleanup verification and, if completed, the verified backup restore result.

Keep keys and personal paths out of frame. Capture each state from the live app; never draw or edit a result into an image. If the mock provider prevents a plan or the live operation fails, do not manufacture the missing plan or success screenshot. Update the optional screenshots section in README only after the files exist. Record a 2–3 minute screen capture following the timed script above, then add a video URL to the Devpost entry only after the video has actually been uploaded and checked.
