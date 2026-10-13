import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { WorkspaceSelector } from './WorkspaceSelector'
import { setMockContext } from '../test/setup'

const scanned = {
  project_path: 'D:/work/second-app', workspace_mode: 'user', project_type: 'python', framework: 'unknown',
  package_manager: 'pip', language: 'python', has_git: false, git_clean: false, git_status: 'not_repository',
  cleanup_candidates: [], total_recoverable_bytes: 0, total_recoverable_human: '0 B', protected_paths: [], notes: '',
  access_grant_id: 'registered-folder-token',
}

describe('WorkspaceSelector', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(globalThis.fetch).mockReset()
    setMockContext()
  })

  it('registers and scans the entered absolute path, then displays workspace and Git state', async () => {
    const setCurrentProject = vi.fn()
    vi.mocked(globalThis.fetch)
      .mockResolvedValueOnce({ ok: true, json: async () => ({ grant_id: 'registered-folder-token', project_path: scanned.project_path }) } as Response)
      .mockResolvedValueOnce({ ok: true, json: async () => scanned } as Response)
    setMockContext({ setCurrentProject })
    render(<WorkspaceSelector />)
    fireEvent.change(screen.getByLabelText(/Select My Project/), { target: { value: scanned.project_path } })
    fireEvent.click(screen.getByRole('button', { name: 'Select My Project' }))

    expect(await screen.findByRole('status')).toHaveTextContent('Folder registered and selected')
    expect(setCurrentProject).toHaveBeenCalledWith(scanned)
    expect(globalThis.fetch).toHaveBeenNthCalledWith(1, '/api/access/grants', expect.objectContaining({ method: 'POST' }))
    expect(globalThis.fetch).toHaveBeenNthCalledWith(2, '/api/scan/', expect.objectContaining({ method: 'POST', body: JSON.stringify({ path: scanned.project_path, access_grant_id: 'registered-folder-token' }) }))
  })

  it('shows an invalid path error and never selects or scans the previous workspace', async () => {
    const previous = { ...scanned, project_path: 'D:/work/previous-project' }
    const setCurrentProject = vi.fn()
    vi.mocked(globalThis.fetch).mockResolvedValueOnce({ ok: false, status: 404, json: async () => ({ detail: 'Project path is unavailable.' }) } as Response)
    setMockContext({ currentProject: previous, setCurrentProject })
    render(<WorkspaceSelector />)
    fireEvent.change(screen.getByLabelText(/Select My Project/), { target: { value: 'D:/work/missing-project' } })
    fireEvent.click(screen.getByRole('button', { name: 'Select My Project' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('previous workspace was not scanned as a fallback')
    expect(globalThis.fetch).toHaveBeenCalledTimes(1)
    expect(setCurrentProject).not.toHaveBeenCalled()
    expect(screen.getByText('D:/work/previous-project')).toBeInTheDocument()
  })
})
