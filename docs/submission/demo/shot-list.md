# Demo shot list

The live application was opened at `http://127.0.0.1:5173` with the backend on loopback port 8000. All workflow shots refer to the synthetic `demo-project` fixture. The browser screenshots below were viewed during the run; screenshot files are not included because this session has no supported browser-screenshot export-to-workspace operation.

| Time | Scene | Live state to show | Recorded/verified status |
|---|---|---|---|
| 0:00–0:20 | Student-builder hook | Text-led opening over the real DevSweep AI interface | Narration copy prepared; no personal-camera footage recorded |
| 0:20–0:38 | Brand and dashboard | Mascot mark, dashboard, Clean. Keep. Restore. | Live app opened; logo visible |
| 0:38–1:00 | Select and scan | Workspace selector, Safe Demo selected, completed scan findings | Live workflow completed; 9 candidates, 138.3 MB candidate estimate |
| 1:00–1:25 | AI analysis | AI Analysis panel with provider/model and actual recommendations | Live Nebius request succeeded; UI reported `nebius` and `nvidia/nemotron-3-super-120b-a12b` |
| 1:25–1:52 | Plan and approval | Cleanup Plans page with only `temp-artifact.tmp`, SAFE, 96 KB, explicit approval control | Live plan created; approval checkbox checked in app |
| 1:52–2:15 | Execution and verification | Execution complete and verification checks | Live: 1/1 item deleted, 0 failed, verification passed; `src` and `package.json` preserved; Git check skipped (fixture is not a Git repository) |
| 2:15–2:32 | Backup and restore | Restore Center, SHA-256-verified backup, completed restore history | Live restore completed; original SHA-256 and file size verified after restore |
| 2:32–2:45 | Close | Mascot, tagline, repository address | Text prepared; MP4 was not recorded |

## Capture notes

- The live scan, plan, verification, and restore screens were displayed through the browser screenshot API during the workflow. They were not exported as files in this environment.
- Three file deliverables named `01-scan-findings.png`, `02-reviewed-plan.png`, and `03-verification-restore.png` still need to be captured with Windows Snipping Tool from the live app. Do not use generated mockups in their place.
- Keep the cursor away from any terminal or secret-bearing settings page. The demo app view did not expose the API key.
- A final MP4 edit was not produced; see `verification-report.md`.
