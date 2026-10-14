# DevSweep AI — Devpost gallery

This gallery combines genuine captures of the running DevSweep AI application with a small number of designed project graphics. The UI screenshots were captured at 1920×1440 from the local React/FastAPI app on 14 October 2026. The cleanup workflow used only the synthetic fixture at `C:\Temp\devsweep-gallery-demo`.

## Recommended Devpost uploads

**Demo video:** [Watch DevSweep AI on YouTube](https://youtu.be/9oGs6lo1hrc). This is the exact link supplied by the project owner; playback was not independently verified during this repository task.

1. `01-cover.png` — designed project cover using the repository mascot.
2. `02-dashboard-live.png` — genuine dashboard screenshot. Persistent activity counts come from the local database and may include earlier runs.
3. `03-workspace-scan.png` — genuine scan review with SAFE and CAUTION classifications and measured synthetic fixture sizes.
4. `04-live-ai-analysis.png` — genuine analysis attributed in the UI to Nebius `nvidia/nemotron-3-super-120b-a12b`.
5. `05-cleanup-plan-approval.png` — genuine item review and cleanup confirmation screen.
6. `06-explicit-execution-approval.png` — genuine plan review with execution approval unchecked and disabled.
7. `07-approved-execution.png` — the same plan after the explicit approval checkbox was selected; the execute button became enabled.
8. `08-cleanup-verification.png` — genuine execution result and backend verification checks.
9. `11-restore-center-live.png` — genuine Restore Center with SHA-256-verified backup contents and completed restore history.

`09-system-architecture.png` and `10-cleanup-workflow.png` are accurate designed diagrams and are optional uploads if the gallery has room. The real application captures are stronger evidence for implemented features.

## Verified demo results

- Live Nebius analysis succeeded with demo/mock mode disabled. The UI identified the provider and model; three generated artifacts were classified SAFE, while the 11 MB `review-me` directory remained CAUTION and was excluded from the plan.
- The app displayed a plan for `.vite`, `coverage`, and `dist` (40.1 KB total) and required an explicit checkbox approval before enabling execution.
- The app reported 3 of 3 items deleted, 0 failed, and 40.1 KB freed. Its post-cleanup verification passed, including checks that `package.json` remained preserved and `src` still existed.
- Restore Center showed SHA-256-verified backups and completed restore records. The `.vite/manifest.json` synthetic artifact was restored and independently measured at 20 bytes with SHA-256 `CA2CEF5D003B5C2E8CC2EC6519AF9DB00EE07533CD72BA925164CF9FDBBB5882`.
- `.vite`, `coverage`, and `dist` were restored from the app-created backups. The synthetic fixture is reusable and was left with those directories present.

No cleanup was run against the repository or a personal project. Screenshots contain no API key, environment values, personal profile path, or unrelated application window. The temp fixture path is intentionally visible as demo context.

## Historical and source assets

`source-assets/designed/` contains older designed summaries and explainers. Their prior verification/test claims are historical, not current-run evidence. They are not recommended as proof of live application behavior. The capture at `source-assets/diagnostics/ai-analysis-failed-live.png` documents an earlier attempt made while the process lacked outbound HTTPS; a later live request succeeded after network access was enabled. It is diagnostic history, not current status.

`source-assets/generate_gallery.py` regenerates the cover and two diagrams while placing other designed cards under `source-assets/designed/`. Genuine application screenshots are captured separately and must not be regenerated from mockups.

At the time of the 14 October 2026 capture, the gallery was assembled from the running app and a synthetic fixture; the screenshots were not generated from mockups. Subsequent application, test, and documentation changes are not depicted by these captures. See the repository root README and judge guide for current validation results. The linked YouTube URL was supplied by the project owner; its playback was not independently verified here.
