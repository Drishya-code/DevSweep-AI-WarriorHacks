# Reproducible demo

This demo uses only the synthetic project in demo-project. Do not select the repository root or a real personal project for destructive operations.

## Prepare and run

1. Copy the repository-root .env.example to .env. Set NEBIUS_API_KEY in the backend environment and set DEVSWEEP_WORKSPACE_ROOT to the absolute repository root. Never copy a real key into a frontend variable or screenshot.
2. From the repository root, run the backend dependency setup documented in README.md. Start the API from backend with `uvicorn main:app --reload`.
3. In a second terminal, install frontend dependencies and run `npm run dev` from frontend.
4. Open http://localhost:5173 and check the provider indicator. If it says mock, the scan and interface can be explored, but an executable plan is unavailable. Do not describe mock output as live AI.
5. Generate or reset the synthetic data from the repository root with `python generate_demo.py`. This resets only known generated directories and the temporary demo artifact under demo-project. It leaves the source and package manifest alone.

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

Capture the running app at the scan/findings stage, the reviewed cleanup plan, and the verification or restore result. Use the operating system screenshot tool and save genuine captures under docs/images. Keep API keys, personal paths, and other private information out of frame. The optional screenshots section in README.md should be updated only after those files exist. Record a 2–3 minute screen capture, upload it to the chosen public video host, and add the verified URL to the Devpost entry.
