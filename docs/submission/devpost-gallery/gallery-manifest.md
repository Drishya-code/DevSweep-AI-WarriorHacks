# Gallery manifest

All genuine application screenshots below were captured at 1920×1440 from the actual local application on 14 October 2026. The demonstrated workspace was the isolated synthetic fixture `C:\Temp\devsweep-gallery-demo`. No repository cleanup was performed.

| File | Asset type | Contents and evidence | Devpost recommendation |
|---|---|---|---|
| `01-cover.png` | Designed graphic | Project mascot, name, and tagline. | Upload |
| `02-dashboard-live.png` | Genuine application screenshot | Live dashboard. Persistent activity counts are local database totals and can include earlier activity. | Upload |
| `03-workspace-scan.png` | Genuine application screenshot | Synthetic fixture scan showing SAFE candidates and an 11 MB CAUTION directory. | Upload |
| `04-live-ai-analysis.png` | Genuine application screenshot | Successful live analysis, attributed in-app to Nebius `nvidia/nemotron-3-super-120b-a12b`, with 3 SAFE candidates selected and the CAUTION directory excluded. | Upload |
| `05-cleanup-plan-approval.png` | Genuine application screenshot | Step 3 confirmation review for 3 SAFE items (40.1 KB) and 0 CAUTION items. | Upload |
| `06-explicit-execution-approval.png` | Genuine application screenshot | Exact backend plan review; execution checkbox is unchecked and execution is disabled. | Upload |
| `07-approved-execution.png` | Genuine application screenshot | Same plan after explicit approval was checked; execution button is enabled. | Upload |
| `08-cleanup-verification.png` | Genuine application screenshot | App reports 3/3 deleted, 0 failed, 40.1 KB freed, and verification passed. Checks show `package.json` preserved and `src` present. | Upload |
| `09-system-architecture.png` | Designed diagram | React/Vite, loopback FastAPI, scoped workspace grants, scanner, optional Nebius, backend plan checks, explicit approval, backup, and restore safeguards. | Optional |
| `10-cleanup-workflow.png` | Designed diagram | Workspace validation through scan, review, approval, backup, cleanup, verification, and restore. | Optional |
| `11-restore-center-live.png` | Genuine application screenshot | Selected synthetic project, backup details marked as SHA-256 verified, and completed restore history. `.vite/manifest.json` was restored (20 bytes; measured SHA-256 `CA2CEF5D003B5C2E8CC2EC6519AF9DB00EE07533CD72BA925164CF9FDBBB5882`). | Upload |

## Additional evidence and provenance

The app-created backups for `.vite`, `coverage`, and `dist` passed the Restore Center’s SHA-256 verification, and all three fixture directories were restored. Backend post-cleanup verification passed. No credentials or environment variable values were displayed or captured.

`source-assets/diagnostics/ai-analysis-failed-live.png` is a genuine screenshot of an earlier failed request made while outbound HTTPS was unavailable to the backend process. It is diagnostic history only and is not recommended for Devpost; live Nebius analysis later succeeded.

Files under `source-assets/designed/` are historical or designed cards, not current application screenshots. In particular, verification and restore summaries there transcribe an earlier report and are superseded for this run by `08-cleanup-verification.png` and `11-restore-center-live.png`.

These screenshots document the 14 October 2026 live application capture and historical synthetic cleanup run. They do not depict the later deterministic no-key plan changes. Automated tests and the production build were run again for the current repository revision; their results are recorded in the root README and judge guide.
