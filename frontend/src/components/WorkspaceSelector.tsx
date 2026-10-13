import { useState } from 'react'
import { FolderOpen, RotateCcw, Sparkles } from 'lucide-react'
import { useDevSweep } from '../context/DevSweepContext'
import type { ScanResponse } from '../types/api'
import { apiErrorMessage, requestJson } from '../utils/api'

function gitLabel(workspace: ScanResponse) {
  switch (workspace.git_status) {
    case 'clean': return 'Git repository · clean'
    case 'uncommitted': return 'Git repository · uncommitted changes'
    case 'unavailable': return 'Git executable unavailable'
    case 'detection_error': return 'Git status could not be determined'
    case 'not_repository':
    default: return 'Not a Git repository'
  }
}

export function WorkspaceSelector({ onReadyChange }: { onReadyChange?: (ready: boolean) => void }) {
  const { currentProject, setCurrentProject, addScanToHistory } = useDevSweep()
  const [path, setPath] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  const selectProject = async () => {
    const requestedPath = path.trim()
    if (!requestedPath || busy) return
    setBusy(true)
    setError(null)
    setNotice(null)
    let grantId: string | undefined
    try {
      const registration = await requestJson<{ grant_id: string; project_path: string }>('/api/access/grants', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ project_path: requestedPath }),
      })
      grantId = registration.grant_id
      const scan = await requestJson<ScanResponse>('/api/scan/', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: registration.project_path, access_grant_id: grantId }),
      })
      setCurrentProject(scan)
      addScanToHistory(scan)
      onReadyChange?.(true)
      setNotice('Folder registered and selected. The scan used the authorized folder path shown below.')
    } catch (selectionError) {
      if (grantId) {
        try { await requestJson(`/api/access/grants/${encodeURIComponent(grantId)}`, { method: 'DELETE' }) } catch { /* expired grants are harmless */ }
      }
      setError(apiErrorMessage(selectionError, 'technical'))
    } finally {
      setBusy(false)
    }
  }

  const tryDemo = async () => {
    if (busy) return
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      const query = currentProject?.workspace_mode === 'demo' && currentProject.access_grant_id
        ? `?access_grant_id=${encodeURIComponent(currentProject.access_grant_id)}` : ''
      const scan = await requestJson<ScanResponse>(`/api/scan/demo${query}`)
      setCurrentProject(scan)
      addScanToHistory(scan)
      onReadyChange?.(true)
      setNotice('Demo Sandbox selected. This fixture is synthetic and separate from your selected projects.')
    } catch (selectionError) {
      setError(apiErrorMessage(selectionError, 'technical'))
    } finally {
      setBusy(false)
    }
  }

  const resetDemo = async () => {
    if (busy || currentProject?.workspace_mode !== 'demo') return
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      const query = currentProject.access_grant_id ? `?access_grant_id=${encodeURIComponent(currentProject.access_grant_id)}` : ''
      await requestJson(`/api/scan/demo/reset${query}`, { method: 'POST' })
      const refreshed = await requestJson<ScanResponse>(`/api/scan/demo${query}`)
      setCurrentProject(refreshed)
      addScanToHistory(refreshed)
      setNotice('Demo Sandbox reset and rescanned. Files outside the dedicated demo-project directory were not targeted.')
    } catch (resetError) {
      setError(apiErrorMessage(resetError, 'technical'))
    } finally {
      setBusy(false)
    }
  }

  return <section aria-label="Workspace selector" className="space-y-3 rounded-xl border border-devsweep-border bg-devsweep-bgSecondary p-4">
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div><h2 className="font-semibold">Workspace</h2><p className="text-xs text-devsweep-textMuted">Choose one authorized local folder or the isolated synthetic sandbox.</p></div>
      {currentProject && <div className="text-right text-xs"><p className="font-semibold">{currentProject.workspace_mode === 'demo' ? 'Demo Sandbox' : 'My Project'}</p><p className="break-all font-mono text-devsweep-textMuted">{currentProject.project_path}</p><p className="mt-1">{currentProject.project_type} · {gitLabel(currentProject)}</p></div>}
    </div>
    <div className="grid gap-3 lg:grid-cols-[1fr_auto_auto]">
      <div>
        <label htmlFor="workspace-path" className="mb-1 block text-xs font-medium">Select My Project · absolute folder path</label>
        <input id="workspace-path" value={path} onChange={event => setPath(event.target.value)} placeholder={currentProject?.workspace_mode === 'user' ? currentProject.project_path : 'C:\\Users\\you\\Projects\\my-app'} className="w-full rounded-lg border border-devsweep-border bg-devsweep-bg px-3 py-2 font-mono text-xs text-devsweep-text placeholder:text-devsweep-textMuted" disabled={busy} />
        <p className="mt-1 text-xs text-devsweep-textMuted">Browsers cannot grant direct filesystem access. Enter the folder path; the backend validates and registers that exact directory.</p>
      </div>
      <button type="button" onClick={() => void selectProject()} disabled={busy || !path.trim()} className="inline-flex items-center justify-center gap-2 self-end rounded-lg bg-devsweep-accent px-3 py-2 text-sm font-medium text-devsweep-bg disabled:opacity-50"><FolderOpen className="h-4 w-4" />{busy ? 'Checking…' : 'Select My Project'}</button>
      <button type="button" onClick={() => void tryDemo()} disabled={busy} className="inline-flex items-center justify-center gap-2 self-end rounded-lg border border-devsweep-border px-3 py-2 text-sm hover:border-devsweep-accent disabled:opacity-50"><Sparkles className="h-4 w-4" />Try Safe Demo</button>
    </div>
    <div className="flex flex-wrap items-center justify-between gap-2 border-t border-devsweep-border pt-3">
      <p className="text-xs text-devsweep-textMuted">Demo Sandbox contains synthetic files for safe review and reset.</p>
      <button type="button" onClick={() => void resetDemo()} disabled={busy || currentProject?.workspace_mode !== 'demo'} className="inline-flex items-center gap-2 rounded-lg border border-devsweep-border px-3 py-1.5 text-xs hover:border-devsweep-warning disabled:opacity-50"><RotateCcw className="h-3.5 w-3.5" />Reset Demo Sandbox</button>
    </div>
    {error && <p role="alert" className="text-sm text-devsweep-danger">Folder selection failed: {error} Your previous workspace was not scanned as a fallback.</p>}
    {notice && <p role="status" className="text-sm text-devsweep-success">{notice}</p>}
  </section>
}
