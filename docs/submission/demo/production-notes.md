# Demo video production notes

## Intended cut

- Duration: 2:45, based on `narration-script.md`.
- Format target: H.264 MP4, 1080p, 30 fps, with readable captions.
- Story: problem, product, isolated workspace scan, live AI analysis, review and explicit approval, verified cleanup, SHA-256 verified restoration, GitHub close.
- Audio: no music. Narration audio has not been generated.

## Capture and export investigation

- The frontend answered at `http://127.0.0.1:5173` during this check. The backend did not answer at `http://127.0.0.1:8000`, so a new live workflow was not attempted.
- Follow-up after OBS installation: OBS Studio is installed at `D:\obs-studio\bin\64bit\obs64.exe` and its process launched. Its local WebSocket control endpoint was not listening, so no scene/source could be configured or recording controlled through that interface. FFmpeg and FFprobe remain unavailable.
- The Windows computer-use package is present, but its capture API could not initialize: `Trusted RPC service is not configured: sky`.
- The browser bridge listed no active tabs for the application and does not expose desktop video recording or a workspace export operation.
- Windows SAPI voice synthesis was attempted earlier and refused with: “No voice installed on the system or none available with the current security setting.” No audio file is included.
- An HTTPS availability check for a portable FFmpeg download failed because outbound socket access is forbidden in this environment. No additional software was downloaded or installed, and no administrator privileges were requested.
- Native browser screenshots are not a substitute for a screen recording. No fabricated interface footage, mock AI response, screenshot sequence, or empty media placeholder was created.

## Verified source footage available

The accompanying `verification-report.md` records the previously completed live synthetic workflow: scan, successful Nebius analysis, review-only plan, explicit approval, cleanup, post-cleanup verification, and restore with a matching SHA-256 hash. It also records that the protected source file and `package.json` hashes were unchanged. Those earlier live states were viewed but were not saved as video frames in this session.

## Deliverables at this point

- `narration-script.md`: timestamped first-person narration draft.
- `captions.srt`: timed captions matching the narration draft; they are not muxed into a video.
- `shot-list.md`: planned scenes and evidence status.
- `verification-report.md`: actual workflow evidence and media limitations.
- `DevSweep-AI-Demo.mp4`: not created. This is intentionally absent rather than an empty or misleading placeholder.
- Narration audio: not created.

## Follow-up after OBS installation (2026-10-13)

- OBS Studio is installed and its process was launched. The trusted Windows capture bridge still fails with `Trusted RPC service is not configured: sky`; the OBS WebSocket endpoint is not listening. I therefore could not select/configure a capture source or control a recording.
- The repo-documented backend and frontend were started in this session. `http://127.0.0.1:8000/health` returned `healthy` with Nebius configured, and `http://127.0.0.1:5173/agent` returned HTTP 200. No new model inference request or cleanup workflow was run in this follow-up.
- The MP4/audio status above is unchanged. The earlier verified synthetic workflow remains evidence from its original run, not a recording made in this session.
- Follow-up diagnosis of the user’s AI error: the restricted backend process failed outbound HTTPS with Windows socket error 10013. After an approved backend restart with outbound access, an unauthenticated probe reached the configured Nebius service (401, as expected without credentials) and one actual analysis of the synthetic demo succeeded (`ai_used=true`, Nebius, `nvidia/nemotron-3-super-120b-a12b`, 9 recommendations). The explicit CORS preflight from `http://127.0.0.1:5174` also returned 200 with the origin and required methods allowed. No cleanup was performed and no code was changed.
- The fixture was reset from `generate_demo.py` and rescanned. It contains nine nonempty candidate groups totaling 138.27 MB. The fresh live AI analysis recommended deletion of the SAFE candidates (`.nyc_output`, `.vite`, `coverage`, `dist`, `node_modules`, and `temp-artifact.tmp`); execution still requires the user’s in-app review and approval. The synthetic files are present for that workflow, but no deletion or restore of this newly reset set was run.

## Remaining production requirement

To complete the MP4, run a permitted desktop recorder against the real browser during a fresh or reset synthetic demo, then export with a locally available MP4 editor/encoder. Review the entire recording for secrets and private paths before sharing it. Do not record cleanup against the real project.
