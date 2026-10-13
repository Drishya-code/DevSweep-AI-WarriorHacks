# Demo verification report

## Live workflow

- **Frontend/backend:** already-running local frontend and backend responded on `127.0.0.1:5173` and `127.0.0.1:8000`; backend health was `healthy`.
- **Workspace:** selected the isolated synthetic fixture at `demo-project`. Its directory resolved within the repository and was not a symlink or junction.
- **Scan:** completed in the application. The scanner reported 9 candidates and 138.3 MB of candidate data (an estimate, not total project size or actual recovered storage): 6 SAFE, 3 CAUTION, 0 DANGEROUS.
- **Provider:** backend health showed Nebius configured. More importantly, an actual analysis request completed in the UI, which reported `Analyzed by nebius (nvidia/nemotron-3-super-120b-a12b)`. This confirms one live inference request succeeded during this run.
- **Plan:** created from the actual analysis. It contained only `temp-artifact.tmp`, SAFE, 96 KB.
- **Approval and cleanup:** the app's explicit approval checkbox was checked. The app reported 1 of 1 items deleted, 0 failed, and 96.0 KB reported freed.
- **Verification:** the app reported verification passed, `package.json: OK (preserved)`, `src` exists, and `package.json` exists. Git integrity was skipped because the synthetic fixture is not itself a Git repository.
- **Backup and restore:** Restore Center showed one backup entry for `temp-artifact.tmp` and reported the full backup passed SHA-256 verification. Restore history reported `Completed` and “Backup content verified and restored without overwriting existing files.” Afterward the file existed at 98,304 bytes with SHA-256 `3CA214406425182510CF49A0EB3EA233D5CA5A81FF4DA343E47762F4DEB982BC`, matching its pre-cleanup hash. Protected `src/App.tsx` and `package.json` hashes also matched their pre-cleanup values.

## Capture and media status

- **Narration script:** prepared in `narration-script.md`.
- **Synthesized narration:** not generated. Windows SAPI enumerated voices but refused synthesis with “No voice installed on the system or none available with the current security setting.” The partial empty WAV was removed.
- **Video:** `DevSweep-AI-Demo.mp4` was not generated. This environment has no screen recorder or MP4 encoder installed/available (`ffmpeg`, `ffprobe`, OBS, and the checked browser/Node encoder packages were unavailable). The available CUA browser can display/capture screenshots but does not provide an export-to-workspace or video-recording operation. Creating a slideshow from fabricated UI would not meet the brief, so no video is claimed.
- **Screenshots:** the genuine live scan, plan, execution/verification, and restore screens were inspected in the browser during this run, but PNG files could not be exported through the available tools. The three screenshot files remain a manual capture step.
- **Audio:** no voiceover or background track was generated. No face footage was recorded.
- **Secrets:** no API key or environment file was opened or included in the screenshots or deliverables.
- **Build/tests:** no application code was changed for the demo recording task. The frontend tests/build were verified in the immediately prior logo change; this turn focused on live workflow verification and submission assets.

## Follow-up capture investigation (2026-10-13)

- The existing frontend answered on `127.0.0.1:5173`; the backend did not answer on `127.0.0.1:8000`. No new cleanup was run.
- At the time of this follow-up, OBS was not available. The user has since installed OBS Studio at `D:\obs-studio\bin\64bit\obs64.exe`, and its process launched. Its WebSocket control endpoint was not listening; FFmpeg and FFprobe remain unavailable.
- The installed Windows computer-use capture bridge could not initialize because its trusted RPC service is not configured. The browser bridge had no active application tab and provides no desktop recording or export-to-workspace operation.
- Windows SAPI voice synthesis had already failed with a system security/voice availability error. No narration audio exists.
- A check for access to a portable FFmpeg download failed because outbound socket access is forbidden. Nothing was downloaded or installed, and administrator privileges were not requested.
- `captions.srt` and `production-notes.md` are now present. The captions track the narration draft and are not attached to a rendered video.
- **Final MP4 remains uncreated.** No fabricated screen footage or mock interactions were used. The live workflow described above was verified in an earlier run; it was not recorded as a video in this session.
- After OBS was installed, its executable was found and launched. The Windows capture bridge still reports `Trusted RPC service is not configured: sky`, and OBS WebSocket control is not active. I could not configure a capture source or start a recording.
- The documented frontend and backend were subsequently started in this session. Frontend `/agent` returned HTTP 200 and backend `/health` returned `healthy` with Nebius configured. No inference or cleanup was run during this service restart.
- The first provider failure was reproduced without a key or project data: the restricted backend could not open an outbound HTTPS socket (`WinError 10013`, socket access forbidden). After an approved restart allowing outbound access, an unauthenticated connectivity probe reached the configured Nebius service (401 expected without credentials), and a real analysis request using only the synthetic demo completed with `ai_used=true`, Nebius / `nvidia/nemotron-3-super-120b-a12b`, and 9 recommendations. The `http://127.0.0.1:5174` CORS preflight returned 200 with the origin and methods allowed. No cleanup or source-code changes were made.
- The demo generator then reset the dedicated synthetic fixture. The read-only scan reported nine nonempty candidate groups totaling 138.27 MB (formatted as 138.3 MB): `node_modules` 76.26 MB, `dist` 14.36 MB, `.vite` 0.96 MB, `logs` 16.20 MB, `cache` 16.53 MB, `coverage` 2.78 MB, `.nyc_output` 0.97 MB, `review-me` 10.12 MB, and `temp-artifact.tmp` 96 KB. A fresh live Nebius analysis recommended DELETE for the safe generated outputs and also recommended the two CAUTION groups; `review-me` was not recommended for deletion. These are recommendations only. No cleanup was executed during this pass, so this reset fixture remains populated and ready for an explicitly approved demo.

## Remaining before submission

1. Capture the scan, plan, and verification/restore screens with Snipping Tool and save the three PNGs listed in `shot-list.md` in this folder.
2. Install or use a trusted screen recorder/MP4 editor on the user's machine, record the genuine workflow from the synthetic fixture, and combine it with `voiceover.wav` and the timestamped script. Keep the final cut between 2:30 and 3:00.
3. Play back the final MP4 and check duration, audio sync, readability, and the visible path/secret area before submitting it.

The completed live workflow is verified, but the final video and saved screenshot files are not yet deliverable artifacts.
