import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AIAgent } from './AIAgent'
import { setMockContext, mockNavigate } from '../test/setup'

const scan = {
  project_path: 'D:/synthetic/demo', project_type: 'React', framework: 'Vite',
  package_manager: 'npm', language: 'TypeScript', has_git: false, git_clean: true,
  cleanup_candidates: [{ path: 'node_modules', risk: 'SAFE', reason: 'Regenerable dependencies.', size_bytes: 4096, size_human: '4 KB' }],
  total_recoverable_bytes: 4096, total_recoverable_human: '4 KB', protected_paths: ['src'], notes: '',
}

describe('AI Agent', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    setMockContext()
    vi.mocked(globalThis.fetch).mockReset()
    Element.prototype.scrollIntoView = vi.fn()
  })

  it('quick scan sends a real chat request and renders returned scan data', async () => {
    vi.mocked(globalThis.fetch).mockResolvedValue(new Response(JSON.stringify({
      response: 'I scanned the synthetic project.', workspace: scan,
      tool_results: [{ name: 'devsweep_scan_workspace', ok: true, summary: 'Real scanner results.' }],
    }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    render(<AIAgent />)
    fireEvent.click(screen.getByRole('button', { name: /Scan Workspace/i }))

    expect(await screen.findByText('Scanned project:')).toBeInTheDocument()
    expect(screen.getByText('D:/synthetic/demo')).toBeInTheDocument()
    expect(screen.getByText('node_modules')).toBeInTheDocument()
    expect(globalThis.fetch).toHaveBeenCalledWith(expect.stringContaining('/api/ai/chat'), expect.objectContaining({ method: 'POST' }))
  })

  it('quick plan displays a review link without triggering execution', async () => {
    const plan = { plan_id: 'plan-review', items: [{ path: 'node_modules', action: 'DELETE', risk: 'SAFE', reason: 'Regenerable.', estimated_bytes: 4096 }], total_safe_bytes: 4096, total_caution_bytes: 0, total_dangerous_bytes: 0, requires_approval: true, warnings: [] }
    vi.mocked(globalThis.fetch).mockResolvedValue(new Response(JSON.stringify({ response: 'Plan ready for review.', plan, tool_results: [{ name: 'devsweep_plan_cleanup', ok: true, summary: 'Created review-only plan.' }] }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    render(<AIAgent />)
    fireEvent.click(screen.getByRole('button', { name: /Create Cleanup Plan/i }))

    expect(await screen.findByText(/Plan plan-review · review only/)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: /Review plan and approval controls/i }))
    await waitFor(() => expect(mockNavigate).toHaveBeenCalledWith('/plans'))
    expect(globalThis.fetch).toHaveBeenCalledTimes(1)
  })

  it('renders assistant Markdown tables, emphasis, and inline code as formatted content', async () => {
    vi.mocked(globalThis.fetch).mockResolvedValue(new Response(JSON.stringify({
      response: 'Scan results:\n\n| Item | Risk | Why flagged |\n|---|---|---|\n| `naturefit` | **CAUTION** | A sizable folder. |',
    }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    render(<AIAgent />)
    fireEvent.change(screen.getByPlaceholderText(/Ask about a permitted project/), { target: { value: 'Explain the scan.' } })
    fireEvent.click(screen.getByRole('button', { name: 'Send message' }))

    const table = await screen.findByRole('table')
    expect(table).toHaveTextContent('Item')
    expect(table).toHaveTextContent('naturefit')
    expect(table.querySelector('strong')).toHaveTextContent('CAUTION')
    expect(table.querySelector('code')).toHaveTextContent('naturefit')
    expect(table).not.toHaveTextContent('|---|')
  })

  it('keeps the conversation visible and collapses workspace controls for a selected project', () => {
    setMockContext({ currentProject: { ...scan, workspace_mode: 'user', git_status: 'clean' } })
    render(<AIAgent />)

    expect(screen.getByText(/Hi, I can scan a permitted project/)).toBeInTheDocument()
    expect(screen.getByTestId('agent-conversation').scrollTop).toBe(0)
    expect(screen.getByText(/My Project · D:\/synthetic\/demo/)).toBeInTheDocument()
    const workspaceDetails = document.querySelector('details') as HTMLDetailsElement
    expect(workspaceDetails.open).toBe(false)

    fireEvent.click(screen.getByText('Change workspace'))
    expect(workspaceDetails.open).toBe(true)
    expect(screen.getByRole('region', { name: 'Workspace selector' })).toBeInTheDocument()
  })

  it('keeps the welcome message visible before a workspace is selected', async () => {
    render(<AIAgent />)

    expect(screen.getByText(/Hi, I can scan a permitted project/)).toBeInTheDocument()
    expect(screen.getByText('No project selected · choose a workspace')).toBeInTheDocument()
    await waitFor(() => expect((document.querySelector('details') as HTMLDetailsElement).open).toBe(false))

    fireEvent.click(screen.getByText('Choose workspace'))
    expect(screen.getByRole('region', { name: 'Workspace selector' })).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText(/Select My Project/), { target: { value: 'D:/synthetic/demo' } })
    const doneButton = screen.getByRole('button', { name: 'Done choosing workspace' })
    expect(doneButton).not.toHaveClass('animate-pulse')
    vi.mocked(globalThis.fetch)
      .mockResolvedValueOnce(new Response(JSON.stringify({ grant_id: 'test-grant', project_path: 'D:/synthetic/demo' }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ ...scan, project_path: 'D:/synthetic/demo', workspace_mode: 'user', access_grant_id: 'test-grant' }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    fireEvent.click(screen.getByRole('button', { name: 'Select My Project' }))
    expect(await screen.findByRole('status')).toHaveTextContent('Folder registered and selected')
    await waitFor(() => expect(doneButton).toHaveClass('animate-pulse'))
    fireEvent.click(screen.getByRole('button', { name: 'Done choosing workspace' }))
    await waitFor(() => expect((document.querySelector('details') as HTMLDetailsElement).open).toBe(false))
  })
})
