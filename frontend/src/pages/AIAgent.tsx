import { FormEvent, useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { cn, formatBytes, generateId } from '../utils/helpers'
import { useDevSweep } from '../context/DevSweepContext'
import { apiErrorMessage, requestJson } from '../utils/api'
import { ChatMessage, ScanResponse } from '../types/api'
import { WorkspaceSelector } from '../components/WorkspaceSelector'
import { Bot, CheckCircle, FileText, Loader2, RotateCcw, Search, Send, ShieldAlert, Trash2 } from 'lucide-react'

type AgentPlanItem = {
  path: string
  action: 'DELETE' | 'KEEP'
  risk: 'SAFE' | 'CAUTION' | 'DANGEROUS'
  effective_risk?: 'SAFE' | 'CAUTION' | 'DANGEROUS'
  reason: string
  estimated_bytes: number
}

type AgentPlan = {
  plan_id: string
  items: AgentPlanItem[]
  total_safe_bytes: number
  total_caution_bytes: number
  total_dangerous_bytes: number
  requires_approval: boolean
  warnings: string[]
}

type AgentBackup = {
  backup_id: string
  execution_id: string
  project_id: string
  path: string
  size_bytes: number
  created_at: string
}

type AgentToolResult = { name: string; ok: boolean; summary: string; status?: number }
type AgentResponse = {
  response: string
  suggestions?: string[]
  workspace?: ScanResponse | null
  plan?: AgentPlan | null
  backups?: AgentBackup[]
  tool_results?: AgentToolResult[]
  diagnostics?: string[]
}
type AgentMessage = ChatMessage & {
  workspace?: ScanResponse
  plan?: AgentPlan
  backups?: AgentBackup[]
  toolResults?: AgentToolResult[]
  diagnostics?: string[]
}

function renderInlineMarkdown(text: string) {
  const tokens = text.split(/(\*\*[^*]+\*\*|`[^`]+`|\*[^*]+\*)/g)
  return tokens.map((token, index) => {
    if (token.startsWith('**') && token.endsWith('**')) return <strong key={index}>{token.slice(2, -2)}</strong>
    if (token.startsWith('`') && token.endsWith('`')) return <code key={index} className="rounded bg-devsweep-bg px-1 py-0.5 font-mono text-[0.9em]">{token.slice(1, -1)}</code>
    if (token.startsWith('*') && token.endsWith('*')) return <em key={index}>{token.slice(1, -1)}</em>
    return token
  })
}

function AssistantText({ content }: { content: string }) {
  const lines = content.split('\n')
  const blocks: JSX.Element[] = []
  let index = 0
  while (index < lines.length) {
    const isTableRow = (line: string) => line.trim().startsWith('|') && line.trim().endsWith('|')
    const isSeparator = (line: string) => isTableRow(line) && /^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$/.test(line.trim())

    if (index + 1 < lines.length && isTableRow(lines[index]) && isSeparator(lines[index + 1])) {
      const cells = (line: string) => line.trim().replace(/^\||\|$/g, '').split('|').map(cell => cell.trim())
      const headers = cells(lines[index])
      index += 2
      const rows: string[][] = []
      while (index < lines.length && isTableRow(lines[index])) rows.push(cells(lines[index++]))
      blocks.push(<div key={`table-${index}`} className="my-3 overflow-x-auto rounded-lg border border-devsweep-border"><table className="w-full border-collapse text-left text-xs"><thead className="bg-devsweep-bg"><tr>{headers.map((header, column) => <th key={column} className="border-b border-devsweep-border px-3 py-2 font-semibold">{renderInlineMarkdown(header)}</th>)}</tr></thead><tbody>{rows.map((row, rowIndex) => <tr key={rowIndex} className="even:bg-devsweep-bg/50">{headers.map((_, column) => <td key={column} className="border-b border-devsweep-border/60 px-3 py-2 align-top">{renderInlineMarkdown(row[column] || '')}</td>)}</tr>)}</tbody></table></div>)
      continue
    }

    const paragraph: string[] = []
    while (index < lines.length && !(index + 1 < lines.length && isTableRow(lines[index]) && isSeparator(lines[index + 1]))) paragraph.push(lines[index++])
    if (paragraph.some(line => line.trim())) blocks.push(<p key={`text-${index}`} className="whitespace-pre-wrap text-sm">{renderInlineMarkdown(paragraph.join('\n'))}</p>)
  }
  return <div className="space-y-2">{blocks}</div>
}

const INITIAL_MESSAGES: AgentMessage[] = [{
  id: generateId(),
  role: 'assistant',
  content: 'Hi, I can scan a permitted project, explain real cleanup candidates, prepare a review-only plan, and find verified backups. I never delete or restore files from chat; those actions require your confirmation in the matching app page.',
  timestamp: new Date(),
}]

const QUICK_ACTIONS = [
  { label: 'Scan Workspace', icon: Search, prompt: 'Scan my current workspace for cleanup opportunities.' },
  { label: 'Create Cleanup Plan', icon: FileText, prompt: 'Create a cleanup plan for my current project.' },
  { label: 'Restore Project', icon: RotateCcw, prompt: 'Find verified backups from my last cleanup.' },
  { label: 'Safe Cleanup', icon: Trash2, prompt: 'Create a review-only plan using SAFE candidates only. Do not delete anything.' },
]

function RiskTag({ risk }: { risk: string }) {
  const style = risk === 'SAFE' ? 'text-devsweep-success bg-devsweep-success/10' : risk === 'CAUTION' ? 'text-devsweep-warning bg-devsweep-warning/10' : 'text-devsweep-danger bg-devsweep-danger/10'
  return <span className={cn('rounded px-2 py-0.5 text-xs font-semibold', style)}>{risk}</span>
}

export function AIAgent() {
  const {
    currentProject, aiProvider, aiModel, realInferenceAvailable,
    setCurrentProject, addScanToHistory, setCurrentPlan,
  } = useDevSweep()
  const navigate = useNavigate()
  const [messages, setMessages] = useState<AgentMessage[]>(INITIAL_MESSAGES)
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [workspaceOptionsOpen, setWorkspaceOptionsOpen] = useState(false)
  const [workspaceReady, setWorkspaceReady] = useState(false)
  const sendLock = useRef(false)
  const messagesContainerRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Keep auto-scroll inside the conversation pane. scrollIntoView can move the
  // app's outer page and hide the agent header/workspace controls on short screens.
  useEffect(() => {
    const container = messagesContainerRef.current
    if (container && (messages.length > 1 || isLoading)) container.scrollTop = container.scrollHeight
  }, [messages, isLoading])

  const sendMessage = async (text: string) => {
    const trimmed = text.trim()
    if (!trimmed || sendLock.current) return
    sendLock.current = true
    setIsLoading(true)
    const userMessage: AgentMessage = { id: generateId(), role: 'user', content: trimmed, timestamp: new Date() }
    setMessages(previous => [...previous, userMessage])
    setInput('')

    try {
      const data = await requestJson<AgentResponse>('/api/ai/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: trimmed,
          history: messages.slice(-10).map(message => ({ role: message.role, content: message.content })),
          project_path: currentProject?.project_path,
          access_grant_id: currentProject?.access_grant_id,
        }),
      })
      if (data.workspace) {
        setCurrentProject(data.workspace)
        addScanToHistory(data.workspace)
      }
      if (data.plan) setCurrentPlan(data.plan)
      const assistant: AgentMessage = {
        id: generateId(), role: 'assistant', content: data.response, timestamp: new Date(),
        workspace: data.workspace || undefined, plan: data.plan || undefined,
        backups: data.backups || [], toolResults: data.tool_results || [], diagnostics: data.diagnostics || [],
      }
      setMessages(previous => [...previous, assistant])
    } catch (error) {
      setMessages(previous => [...previous, {
        id: generateId(), role: 'assistant', content: apiErrorMessage(error, 'technical'), timestamp: new Date(),
      }])
    } finally {
      sendLock.current = false
      setIsLoading(false)
    }
  }

  const handleSend = (event: FormEvent) => {
    event.preventDefault()
    void sendMessage(input)
  }

  const renderWorkspace = (workspace: ScanResponse) => (
    <section aria-label="Actual scan findings" className="mt-3 space-y-3 border-t border-devsweep-border pt-3">
      <div className="break-all text-xs text-devsweep-textMuted">Scanned project: <span className="font-mono text-devsweep-textSecondary">{workspace.project_path}</span></div>
      <p className="text-sm">{workspace.project_type} · {workspace.framework} · {workspace.cleanup_candidates.length} candidates · {workspace.total_recoverable_human} estimated candidate data</p>
      {workspace.cleanup_candidates.length ? <ul className="space-y-2">
        {workspace.cleanup_candidates.slice(0, 30).map(candidate => (
          <li key={candidate.path} className="flex flex-wrap items-start justify-between gap-2 rounded-lg bg-devsweep-bg p-3 text-sm">
            <div className="min-w-0 flex-1">
              <p className="break-all font-mono">{candidate.path}</p>
              <p className="mt-1 text-xs text-devsweep-textSecondary">{candidate.reason}</p>
            </div>
            <div className="flex shrink-0 items-center gap-2"><RiskTag risk={candidate.risk} /><span className="text-xs text-devsweep-textMuted">{formatBytes(candidate.size_bytes)}</span></div>
          </li>
        ))}
        {workspace.cleanup_candidates.length > 30 && <li className="text-xs text-devsweep-textMuted">Showing 30 of {workspace.cleanup_candidates.length} candidates.</li>}
      </ul> : <p className="text-sm text-devsweep-textSecondary">The scanner found no cleanup candidates.</p>}
      {workspace.protected_paths.length > 0 && <p className="flex gap-2 text-xs text-devsweep-success"><ShieldAlert className="h-4 w-4 shrink-0" />Protected paths detected: {workspace.protected_paths.join(', ')}</p>}
      {workspace.notes && <p className="text-xs text-devsweep-textMuted">{workspace.notes}</p>}
    </section>
  )

  const renderPlan = (plan: AgentPlan) => (
    <section aria-label="Review-only cleanup plan" className="mt-3 space-y-3 border-t border-devsweep-border pt-3">
      <p className="flex items-center gap-2 text-sm font-semibold"><CheckCircle className="h-4 w-4 text-devsweep-success" />Plan {plan.plan_id} · review only</p>
      <p className="text-sm">SAFE {formatBytes(plan.total_safe_bytes)} · CAUTION {formatBytes(plan.total_caution_bytes)} · DANGEROUS {formatBytes(plan.total_dangerous_bytes)}</p>
      <ul className="space-y-2">
        {plan.items.map((item, index) => <li key={`${item.path}-${index}`} className="flex flex-wrap justify-between gap-2 rounded-lg bg-devsweep-bg p-3 text-sm">
          <div><p className="break-all font-mono">{item.path} <span className="font-sans">· {item.action}</span></p><p className="text-xs text-devsweep-textSecondary">{item.reason}</p></div>
          <span className="flex items-center gap-2"><RiskTag risk={item.effective_risk || item.risk} />{formatBytes(item.estimated_bytes)}</span>
        </li>)}
      </ul>
      {plan.warnings.map((warning, index) => <p key={index} className="text-xs text-devsweep-warning">{warning}</p>)}
      <button type="button" onClick={() => navigate('/plans')} className="rounded-lg bg-devsweep-accent px-3 py-2 text-sm font-medium text-devsweep-bg hover:bg-devsweep-accentHover">Review plan and approval controls</button>
      <p className="text-xs text-devsweep-textMuted">No files were changed by creating this plan.</p>
    </section>
  )

  const renderBackups = (backups: AgentBackup[]) => (
    <section aria-label="Verified restore backups" className="mt-3 space-y-2 border-t border-devsweep-border pt-3">
      {backups.length ? backups.map(backup => <div key={backup.backup_id} className="rounded-lg bg-devsweep-bg p-3 text-sm">
        <p className="break-all font-mono">{backup.path}</p>
        <p className="mt-1 text-xs text-devsweep-textMuted">Verified backup · {formatBytes(backup.size_bytes)} · {new Date(backup.created_at).toLocaleString()}</p>
      </div>) : <p className="text-sm text-devsweep-textSecondary">No verified backups were found for this project.</p>}
      <button type="button" onClick={() => navigate('/restore')} className="rounded-lg border border-devsweep-border px-3 py-2 text-sm hover:border-devsweep-accent">Review Restore Center</button>
      <p className="text-xs text-devsweep-textMuted">A restore requires content review and your confirmation in Restore Center.</p>
    </section>
  )

  return (
    <div className="flex h-full min-h-0 min-w-0 flex-col animate-in">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b border-devsweep-border bg-devsweep-bgSecondary p-4">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-devsweep-accent/10"><Bot className="h-5 w-5 text-devsweep-accent" /></div>
          <div><h1 className="text-lg font-semibold">DevSweep AI Agent</h1><p className="text-xs text-devsweep-textMuted">{aiProvider} · {aiModel} · {realInferenceAvailable ? 'Provider configured; live inference not verified' : 'Live provider not configured'}</p></div>
        </div>
        <div className="text-right text-xs">
          <p className="font-medium">{currentProject ? 'Selected workspace' : 'No project selected'}</p>
          <p className="text-devsweep-textMuted">{currentProject ? `${currentProject.workspace_mode === 'demo' ? 'Demo Sandbox' : 'My Project'} · ${currentProject.project_type}` : 'Choose a project or use the configured workspace'}</p>
        </div>
      </header>

      <details open={workspaceOptionsOpen} className="rounded-xl border border-devsweep-border bg-devsweep-bgSecondary">
        <summary onClick={event => { event.preventDefault(); if (!workspaceOptionsOpen) setWorkspaceReady(false); setWorkspaceOptionsOpen(!workspaceOptionsOpen) }} className="flex cursor-pointer list-none flex-wrap items-center justify-between gap-2 px-4 py-3 [&::-webkit-details-marker]:hidden">
          <span className="font-semibold">Workspace</span>
          <span className="min-w-0 break-all text-right font-mono text-xs text-devsweep-textMuted">
            {currentProject ? `${currentProject.workspace_mode === 'demo' ? 'Demo Sandbox' : 'My Project'} · ${currentProject.project_path}` : 'No project selected · choose a workspace'}
          </span>
          <span className="text-xs text-devsweep-accent">{currentProject ? 'Change workspace' : 'Choose workspace'}</span>
        </summary>
        <div className="border-t border-devsweep-border p-3">
          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
            <p className="text-xs text-devsweep-textMuted">Choose a workspace, then return here to chat.</p>
            <button type="button" onClick={() => setWorkspaceOptionsOpen(false)} className={cn('rounded-lg border px-3 py-1.5 text-xs font-medium transition-all hover:border-devsweep-accent', workspaceReady && 'animate-pulse border-devsweep-accent bg-devsweep-accent text-devsweep-bg shadow-[0_0_18px_rgba(59,130,246,0.65)] ring-2 ring-devsweep-accent/50')}>Done choosing workspace</button>
          </div>
          <WorkspaceSelector onReadyChange={setWorkspaceReady} />
        </div>
      </details>

      <div ref={messagesContainerRef} data-testid="agent-conversation" className="min-h-0 flex-1 space-y-4 overflow-y-auto p-4">
        {messages.map(message => <article key={message.id} className={cn('flex gap-3', message.role === 'user' && 'flex-row-reverse')}>
          <div className={cn('flex h-8 w-8 shrink-0 items-center justify-center rounded-lg', message.role === 'assistant' ? 'bg-devsweep-accent/10 text-devsweep-accent' : 'bg-devsweep-bgTertiary text-devsweep-textSecondary')}>
            {message.role === 'assistant' ? <Bot className="h-4 w-4" /> : <span className="text-xs font-medium">U</span>}
          </div>
          <div className={cn('max-w-[85%] rounded-2xl px-4 py-3', message.role === 'assistant' ? 'border border-devsweep-border bg-devsweep-bgSecondary text-devsweep-text' : 'bg-devsweep-accent text-devsweep-bg')}>
            <AssistantText content={message.content} />
            {message.workspace && renderWorkspace(message.workspace)}
            {message.plan && renderPlan(message.plan)}
            {message.backups && message.toolResults?.some(result => result.name === 'devsweep_restore_guidance') && renderBackups(message.backups)}
            {message.diagnostics && message.diagnostics.length > 0 && <details className="mt-3 border-t border-devsweep-border pt-2 text-xs text-devsweep-textMuted">
              <summary className="cursor-pointer">Technical details</summary><ul className="mt-2 list-disc space-y-1 pl-5">{message.diagnostics.map((item, index) => <li key={index}>{item}</li>)}</ul>
            </details>}
            {message.toolResults && message.toolResults.length > 0 && <details className="mt-3 text-xs text-devsweep-textMuted">
              <summary className="cursor-pointer">Tool activity ({message.toolResults.length})</summary>
              <ul className="mt-2 space-y-1">{message.toolResults.map((result, index) => <li key={index} className={result.ok ? 'text-devsweep-success' : 'text-devsweep-warning'}>{result.name}: {result.summary}</li>)}</ul>
            </details>}
            <div className="mt-2 text-right text-[10px] text-devsweep-textMuted">{message.timestamp.toLocaleTimeString()}</div>
          </div>
        </article>)}
        {isLoading && <div role="status" className="flex items-center gap-2 text-sm text-devsweep-textMuted"><Loader2 className="h-4 w-4 animate-spin" />Running permitted workspace tools and preparing a response…</div>}
      </div>

      <footer className="border-t border-devsweep-border bg-devsweep-bgSecondary p-4">
        <div className="mb-3 flex flex-wrap gap-2">
          {QUICK_ACTIONS.map(action => <button key={action.label} type="button" onClick={() => void sendMessage(action.prompt)} disabled={isLoading} className="flex items-center gap-1.5 rounded-lg border border-devsweep-border bg-devsweep-bg px-3 py-1.5 text-xs hover:border-devsweep-accent/50 disabled:opacity-50">
            <action.icon className="h-3 w-3" />{action.label}
          </button>)}
        </div>
        <form onSubmit={handleSend} className="flex gap-2">
          <textarea ref={textareaRef} value={input} onChange={event => setInput(event.target.value)} placeholder="Ask about a permitted project, cleanup candidates, a plan, or verified backups…" className="min-h-[44px] max-h-32 flex-1 resize-none rounded-lg border border-devsweep-border bg-devsweep-bg px-4 py-2 text-devsweep-text placeholder-devsweep-textMuted focus:border-devsweep-accent focus:outline-none focus:ring-1 focus:ring-devsweep-accent" rows={1} disabled={isLoading} />
          <button type="submit" disabled={!input.trim() || isLoading} aria-label="Send message" className="mb-1 flex items-center gap-2 self-end rounded-lg bg-devsweep-accent px-4 py-2 font-medium text-devsweep-bg hover:bg-devsweep-accentHover disabled:cursor-not-allowed disabled:opacity-50">
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </button>
        </form>
      </footer>
    </div>
  )
}
