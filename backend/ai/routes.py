"""AI Agent API routes."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Dict, Any, Literal
import asyncio
import uuid
import json
import logging
import time
import re

from ai.factory import get_ai_provider
from ai.nebius_provider import NebiusProvider
from ai.prompts import CHAT_SYSTEM_PROMPT, DEVSWEEP_SYSTEM_PROMPT
from scanner.detector import analyze_project, RiskLevel
from config import settings
from pathlib import Path
from security.workspace_access import ProjectAuthorization, ProjectAccessError, authorize_project_path


router = APIRouter(tags=["ai"])


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str
    history: List[ChatMessage] = Field(default_factory=list)
    project_path: Optional[str] = None
    access_grant_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    suggestions: List[str] = Field(default_factory=list)
    workspace: Optional[Dict[str, Any]] = None
    plan: Optional[Dict[str, Any]] = None
    backups: List[Dict[str, Any]] = Field(default_factory=list)
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)
    diagnostics: List[str] = Field(default_factory=list)


class AgentToolArguments(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ScanWorkspaceArguments(AgentToolArguments):
    path: Optional[str] = None


class PlanCleanupArguments(AgentToolArguments):
    path: Optional[str] = None
    safe_only: bool = False


class ExplainCandidateArguments(AgentToolArguments):
    path: Optional[str] = None


class RestoreGuidanceArguments(AgentToolArguments):
    path: Optional[str] = None


AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "devsweep_scan_workspace",
            "description": "Run the real deterministic scanner on the selected or explicitly named permitted project. This only reads and reports; it never deletes files.",
            "parameters": {
                "type": "object", "properties": {"path": {"type": "string", "description": "Optional absolute project folder. Omit to use the currently selected project."}}, "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "devsweep_plan_cleanup",
            "description": "Scan and analyze the selected or explicitly named project, then create a review-only cleanup plan through backend safety checks. Never execute it.",
            "parameters": {
                "type": "object", "properties": {
                    "path": {"type": "string", "description": "Optional absolute project folder. Omit to use the currently selected project."},
                    "safe_only": {"type": "boolean", "description": "Include only candidates whose scanner and AI risks are both SAFE."},
                }, "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "devsweep_explain_candidate",
            "description": "Explain a candidate from a fresh real scan of the selected project. Requires its exact candidate path; does not inspect arbitrary files or delete anything.",
            "parameters": {
                "type": "object", "properties": {"path": {"type": "string", "description": "Exact relative candidate path from the scanner."}}, "required": ["path"], "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "devsweep_restore_guidance",
            "description": "List actual verified backups for the selected project. Restoration itself must be reviewed and explicitly confirmed in Restore Center.",
            "parameters": {
                "type": "object", "properties": {"path": {"type": "string", "description": "Optional project folder. Omit to use the currently selected project."}}, "additionalProperties": False,
            },
        },
    },
]

_AGENT_TOOL_MODELS = {
    "devsweep_scan_workspace": ScanWorkspaceArguments,
    "devsweep_plan_cleanup": PlanCleanupArguments,
    "devsweep_explain_candidate": ExplainCandidateArguments,
    "devsweep_restore_guidance": RestoreGuidanceArguments,
}
MAX_TOOL_ROUNDS = 4
MAX_TOOL_CALLS_PER_ROUND = 4
AI_CHAT_TIMEOUT_SECONDS = 30
AGENT_TOOL_TIMEOUT_SECONDS = 45


class AnalyzeRequest(BaseModel):
    project_path: str
    access_grant_id: Optional[str] = None


class AnalyzeResponse(BaseModel):
    project_type: str
    framework: str
    package_manager: str
    language: str
    candidates: List[Dict[str, Any]]
    total_recoverable: int
    total_recoverable_human: str
    ai_used: bool = False  # True only after successful Nebius inference
    provider_name: str = "mock"
    model: str = "unknown"
    demo_mode: bool = False
    analysis_id: Optional[str] = None


# Short-lived, in-process proof that the submitted candidates came from successful
# Nebius inference. Cleanup plan creation consumes this server-side result.
_verified_analyses: Dict[str, Dict[str, Any]] = {}
VERIFIED_ANALYSIS_TTL_SECONDS = 15 * 60


def take_verified_analysis(
    analysis_id: str,
    project_path: Path | ProjectAuthorization,
) -> Optional[Dict[str, Any]]:
    result = _verified_analyses.pop(analysis_id, None)
    if not result or result.get("expires_at", 0) <= time.monotonic():
        return None
    saved_authorization: ProjectAuthorization = result["authorization"]
    try:
        saved_authorization.revalidate()
    except ProjectAccessError:
        return None
    if isinstance(project_path, ProjectAuthorization):
        if project_path != saved_authorization:
            return None
        try:
            project_path.revalidate()
        except ProjectAccessError:
            return None
    else:
        try:
            requested_authorization = authorize_project_path(
                str(project_path),
                saved_authorization.grant_id,
            )
        except ProjectAccessError:
            return None
        if requested_authorization != saved_authorization:
            return None
    return result


def format_bytes(bytes_val: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} PB"


@router.post("/chat", response_model=ChatResponse)
async def ai_chat(request: ChatRequest):
    """Chat with the AI agent and execute only its bounded, read/plan tools."""
    from ai.provider import ChatMessage as ProviderChatMessage, MockProvider

    try:
        provider = get_ai_provider()
    except Exception as exc:
        logging.getLogger(__name__).error("AI provider initialization failed: %s", type(exc).__name__)
        raise HTTPException(status_code=503, detail="Nebius provider configuration failed. Check backend configuration.") from exc

    context: Optional[str] = None
    configured_workspace = str(Path(settings.workspace_root).resolve())
    if request.project_path:
        try:
            authorization = authorize_project_path(request.project_path, request.access_grant_id)
        except ProjectAccessError as exc:
            raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
        path = authorization.canonical_path
        try:
            analysis = analyze_project(path)
            authorization.revalidate()
        except ProjectAccessError as exc:
            raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
        candidates = [
            {"path": item.path, "risk": item.risk.value, "reason": item.reason, "size_bytes": item.size_bytes}
            for item in analysis.cleanup_candidates
        ]
        context = json.dumps({
            "selected_project": str(path),
            "project_type": analysis.project_type.value,
            "framework": analysis.framework,
            "package_manager": analysis.package_manager,
            "language": analysis.language,
            "has_git": analysis.has_git,
            "git_clean": analysis.git_clean,
            "cleanup_candidates": candidates,
            "protected_paths": analysis.protected_paths,
            "total_recoverable_bytes": analysis.total_recoverable_bytes,
        })
    else:
        # Server-configured default; tool execution still applies path authorization.
        context = json.dumps({"configured_workspace_root": configured_workspace})

    system_prompt = CHAT_SYSTEM_PROMPT + """

The application supplies a small set of DevSweep tools. Use them for actual scan,
cleanup-plan, candidate-explanation, and verified-backup information. The selected
project context is the only default path. If the user names a different path, pass
that exact path to the tool; never silently substitute the selected project when
that path is invalid or unauthorized. Tool output is authoritative: do not invent
paths, sizes, risks, plan IDs, backup records, or success. A plan is review-only.
You do not have an execution or restoration tool. The user must review a plan in
Cleanup Plans and explicitly approve it, or review/confirm a restore in Restore
Center. Do not claim an operation occurred unless the tool result says it did.
If arguments are omitted, use selected project context; otherwise ask a follow-up.
"""
    messages = [ProviderChatMessage(role="system", content=system_prompt)]
    if context:
        messages.append(ProviderChatMessage(role="system", content=f"Trusted server-generated selected-project scan context: {context}"))
    messages.extend(ProviderChatMessage(role=item.role, content=item.content) for item in request.history[-10:])
    messages.append(ProviderChatMessage(role="user", content=request.message))

    workspace_result: Optional[Dict[str, Any]] = None
    plan_result: Optional[Dict[str, Any]] = None
    backups_result: List[Dict[str, Any]] = []
    tool_results: List[Dict[str, Any]] = []
    diagnostics: List[str] = []
    executed: Dict[str, Dict[str, Any]] = {}

    # In mock mode, support only clear app intents through real backend tools.
    # The mock model itself never fabricates scan, plan, or restore data.
    first_response = None
    if isinstance(provider, MockProvider):
        fallback_tool = _intent_tool(request.message)
        if fallback_tool:
            requested_path = _extract_requested_path(request.message)
            arguments = {"path": requested_path} if requested_path else {}
            try:
                fallback_result = await _dispatch_agent_tool(fallback_tool, arguments, request, request.message)
            except HTTPException as exc:
                fallback_result = {"ok": False, "summary": str(exc.detail), "status": exc.status_code}
            except Exception as exc:
                logging.getLogger(__name__).warning("Agent tool failed: %s", type(exc).__name__)
                fallback_result = {"ok": False, "summary": "The requested operation failed safely. Retry or use the matching workspace page."}
            first_response = (fallback_tool, fallback_result)
    if first_response:
        tool_name, tool_result = first_response
        tool_results.append({"name": tool_name, **tool_result})
        workspace_result = tool_result.get("workspace")
        plan_result = tool_result.get("plan")
        backups_result = tool_result.get("backups", [])
        response_text = _format_tool_result(tool_name, tool_result)
        return ChatResponse(response=response_text, workspace=workspace_result, plan=plan_result, backups=backups_result, tool_results=tool_results)

    try:
        for round_index in range(MAX_TOOL_ROUNDS):
            response = await asyncio.wait_for(
                provider.chat_completion(messages, tools=AGENT_TOOLS, tool_choice="auto"),
                timeout=AI_CHAT_TIMEOUT_SECONDS,
            )
            calls, malformed = _extract_tool_calls(response)
            if malformed:
                diagnostics.append("Model returned a malformed tool-call payload.")
                return ChatResponse(
                    response="I couldn’t safely interpret that tool request. Please restate what you want me to do.",
                    workspace=workspace_result, plan=plan_result, backups=backups_result,
                    tool_results=tool_results, diagnostics=diagnostics,
                )
            if not calls:
                if request.project_path:
                    authorization.revalidate()
                answer = response.content.strip()
                if _looks_like_tool_payload(answer):
                    diagnostics.append("Raw tool-call JSON was suppressed instead of being shown as an assistant answer.")
                    answer = "I received an incomplete tool request and did not run it. Please try again or choose a workspace first."
                return ChatResponse(
                    response=answer or "I couldn’t produce a response. Please try a more specific request.",
                    workspace=workspace_result, plan=plan_result, backups=backups_result,
                    tool_results=tool_results, diagnostics=diagnostics,
                )

            messages.append(ProviderChatMessage(role="assistant", content=response.content or "", tool_calls=calls))
            for call_index, call in enumerate(calls):
                call_id = call["id"]
                function = call.get("function") or {}
                name = function.get("name", "")
                raw_arguments = function.get("arguments", "{}")
                try:
                    if isinstance(raw_arguments, str):
                        arguments = json.loads(raw_arguments)
                    else:
                        arguments = raw_arguments
                    if not isinstance(arguments, dict):
                        raise ValueError("Tool arguments must be a JSON object.")
                    key = json.dumps([name, arguments], sort_keys=True, separators=(",", ":"))
                    if call_index >= MAX_TOOL_CALLS_PER_ROUND:
                        result = {"ok": False, "summary": "The request exceeded the per-turn tool limit."}
                    elif key in executed:
                        result = executed[key]
                        diagnostics.append(f"Repeated {name or 'unknown'} call reused its earlier result.")
                    else:
                        result = await asyncio.wait_for(
                            _dispatch_agent_tool(name, arguments, request, request.message),
                            timeout=AGENT_TOOL_TIMEOUT_SECONDS,
                        )
                        executed[key] = result
                except (json.JSONDecodeError, ValueError) as exc:
                    result = {"ok": False, "summary": str(exc)}
                except HTTPException as exc:
                    result = {"ok": False, "summary": exc.detail, "status": exc.status_code}
                except Exception as exc:
                    logging.getLogger(__name__).warning("Agent tool failed: %s", type(exc).__name__)
                    result = {"ok": False, "summary": "The requested operation failed safely. Retry or use the matching workspace page."}
                    diagnostics.append(f"{name or 'unknown'} returned {type(exc).__name__}.")

                tool_results.append({"name": name or "unknown", **result})
                workspace_result = result.get("workspace", workspace_result)
                plan_result = result.get("plan", plan_result)
                backups_result = result.get("backups", backups_result)
                messages.append(ProviderChatMessage(
                    role="tool", tool_call_id=call_id,
                    content=json.dumps(_model_safe_tool_result(result), ensure_ascii=False),
                ))
        diagnostics.append("The model exceeded the bounded tool-calling cycle.")
        return ChatResponse(
            response="I couldn’t finish the request within the safe tool limit. Review the results above or try a more focused request.",
            workspace=workspace_result, plan=plan_result, backups=backups_result,
            tool_results=tool_results, diagnostics=diagnostics,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logging.getLogger(__name__).warning("AI chat completion failed: %s", type(exc).__name__)
        raise HTTPException(status_code=502, detail=f"AI request failed: {type(exc).__name__}") from exc


def _looks_like_tool_payload(content: str) -> bool:
    return content.lstrip().startswith("{") and '"tool"' in content and '"arguments"' in content


def _extract_tool_calls(response: Any) -> tuple[List[Dict[str, Any]], bool]:
    calls = getattr(response, "tool_calls", None)
    if calls:
        if not isinstance(calls, list):
            return [], True
        normalized = []
        for call in calls:
            if not isinstance(call, dict):
                return [], True
            function = call.get("function")
            if not isinstance(function, dict) or not isinstance(function.get("name"), str):
                return [], True
            normalized.append({
                "id": str(call.get("id") or f"call_{uuid.uuid4().hex}"),
                "type": "function",
                "function": {"name": function["name"], "arguments": function.get("arguments", "{}") if isinstance(function.get("arguments", "{}"), str) else json.dumps(function.get("arguments", {}))},
            })
        return normalized, False

    content = (getattr(response, "content", "") or "").strip()
    candidate = content
    if candidate.startswith("```json") and candidate.endswith("```"):
        candidate = candidate[7:-3].strip()
    elif candidate.startswith("```") and candidate.endswith("```"):
        candidate = candidate[3:-3].strip()
    if not candidate.startswith("{"):
        return [], False
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError:
        return [], _looks_like_tool_payload(content)
    if isinstance(payload, dict) and "tool" in payload:
        if not isinstance(payload.get("tool"), str):
            return [], True
        return [{
            "id": f"call_{uuid.uuid4().hex}",
            "type": "function",
            "function": {"name": payload["tool"], "arguments": payload.get("arguments", "{}") if isinstance(payload.get("arguments", {}), str) else json.dumps(payload.get("arguments", {}))},
        }], False
    return [], False


def _intent_tool(message: str) -> Optional[str]:
    text = message.lower()
    if re.search(r"\b(restore|recover|backup)\b", text):
        return "devsweep_restore_guidance"
    if re.search(r"\b(why|explain)\b", text) and re.search(r"\b(candidate|folder|directory|file|remove|delete)\b", text):
        return "devsweep_explain_candidate"
    if re.search(r"\b(plan)\b", text):
        return "devsweep_plan_cleanup"
    if re.search(r"\b(scan|find|identify)\b", text):
        return "devsweep_scan_workspace"
    if re.search(r"\b(what can i|what can we|what is safe|what's safe|safely|safe to)\b", text) and re.search(r"\b(remove|delete|clean)\b", text):
        return "devsweep_scan_workspace"
    if re.search(r"\b(clean|cleanup)\b", text):
        return "devsweep_plan_cleanup"
    return None


def _extract_requested_path(message: str) -> Optional[str]:
    """Extract only an explicitly written absolute path; authorization remains server-side."""
    match = re.search(r"(?<![\w])(?:[A-Za-z]:\\|/)[^\r\n\"'<>]+", message)
    if not match:
        return None
    path = match.group(0).strip().rstrip(".,;:!?)]}")
    return path or None


def _format_tool_result(name: str, result: Dict[str, Any]) -> str:
    if not result.get("ok"):
        return result.get("summary", "The requested operation failed safely.")
    if name == "devsweep_scan_workspace":
        workspace = result.get("workspace") or {}
        candidates = workspace.get("cleanup_candidates", [])
        return f"Scanned {workspace.get('project_path', 'the selected project')}. The scanner found {len(candidates)} cleanup candidates and estimates {workspace.get('total_recoverable_human', 'an unknown amount')} in candidate data. Review the findings below; nothing was deleted."
    if name == "devsweep_plan_cleanup":
        plan = result.get("plan") or {}
        return f"Created review-only cleanup plan {plan.get('plan_id', '')} with {len(plan.get('items', []))} items. Review it in Cleanup Plans and approve there if you want to proceed. Nothing was deleted."
    if name == "devsweep_restore_guidance":
        backups = result.get("backups", [])
        return f"Found {len(backups)} verified restore backup(s) for this project. Review contents and confirm any restore in Restore Center. I did not restore anything."
    return result.get("summary", "Here is the result from the current project scan.")


def _model_safe_tool_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """Exclude access-grant tokens and keep model context bounded."""
    safe = {key: value for key, value in result.items() if key not in {"access_grant_id"}}
    workspace = safe.get("workspace")
    if isinstance(workspace, dict):
        workspace = {key: value for key, value in workspace.items() if key != "access_grant_id"}
        candidates = workspace.get("cleanup_candidates")
        if isinstance(candidates, list) and len(candidates) > 100:
            workspace["cleanup_candidates"] = candidates[:100]
            workspace["candidate_count"] = len(candidates)
        safe["workspace"] = workspace
    return safe


async def _dispatch_agent_tool(name: str, raw_arguments: Dict[str, Any], request: ChatRequest, user_message: str) -> Dict[str, Any]:
    model = _AGENT_TOOL_MODELS.get(name)
    if model is None:
        return {"ok": False, "summary": f"Unsupported tool '{name}'. No operation was run."}
    try:
        arguments = model.model_validate(raw_arguments)
    except Exception:
        return {"ok": False, "summary": "Tool arguments did not match the supported schema. No operation was run."}

    path_was_set = "path" in arguments.model_fields_set and arguments.path is not None
    target_path = arguments.path if path_was_set else (request.project_path or str(settings.workspace_root))
    if not target_path:
        return {"ok": False, "summary": "Select a project in Projects or Scan Workspace, or provide an absolute project folder inside the configured workspace."}
    grant_id = request.access_grant_id if target_path == request.project_path else None

    from scanner.routes import ScanRequest, scan_workspace
    from fastapi import HTTPException as FastAPIHTTPException

    if name in {"devsweep_scan_workspace", "devsweep_plan_cleanup", "devsweep_explain_candidate"}:
        scan = await scan_workspace(ScanRequest(path=target_path, access_grant_id=grant_id))
        workspace = scan.model_dump()
        if name == "devsweep_scan_workspace":
            return {"ok": True, "summary": "Real scanner results.", "workspace": workspace}
        if name == "devsweep_explain_candidate":
            if not path_was_set or not arguments.path:
                return {"ok": False, "summary": "Which candidate path should I explain? Choose an exact path from the fresh scan results.", "workspace": workspace}
            candidate = next((item for item in workspace["cleanup_candidates"] if item["path"] == arguments.path), None)
            if not candidate:
                return {"ok": False, "summary": "That path is not a cleanup candidate in the fresh scan. I did not inspect or change it.", "workspace": workspace}
            return {"ok": True, "summary": "Explanation from the real scanner candidate.", "workspace": workspace, "candidate": candidate}

        analysis = await ai_analyze(AnalyzeRequest(project_path=scan.project_path, access_grant_id=scan.access_grant_id))
        if not analysis.ai_used or not analysis.analysis_id:
            return {
                "ok": False,
                "status": 403,
                "summary": "A cleanup plan requires a successful live Nebius analysis. The project was scanned, but no plan was created because this provider did not return a verified analysis.",
                "workspace": workspace,
            }
        safe_only = arguments.safe_only or bool(re.search(r"\b(safe[- ]only|only\s+safe|safe cleanup|clean only safe)\b", user_message, re.IGNORECASE))
        selected = [
            item for item in analysis.candidates
            if item.get("action") == "DELETE"
            and (not safe_only or (item.get("risk") == "SAFE" and item.get("ai_risk", "SAFE") == "SAFE"))
        ]
        if not selected:
            _verified_analyses.pop(analysis.analysis_id, None)
            return {"ok": True, "summary": "No candidates met the requested criteria, so no cleanup plan was created.", "workspace": workspace, "selected_count": 0}

        from cleanup.routes import CleanupItemRequest, CleanupPlanRequest, create_cleanup_plan
        plan = await create_cleanup_plan(CleanupPlanRequest(
            project_path=scan.project_path,
            access_grant_id=scan.access_grant_id,
            analysis_id=analysis.analysis_id,
            scan_id=scan.scan_id,
            items=[CleanupItemRequest(
                path=item["path"], action=item["action"], risk=item["risk"],
                ai_risk=item.get("ai_risk"), reason=item["reason"], estimated_bytes=item["size_bytes"],
            ) for item in selected],
        ))
        return {"ok": True, "summary": "Review-only plan created by the authorized backend plan route.", "workspace": workspace, "plan": plan.model_dump(), "safe_only": safe_only}

    if name == "devsweep_restore_guidance":
        authorization = authorize_project_path(target_path, grant_id)
        authorization.revalidate()
        from persistence.database import persistence, project_key
        backups = await persistence.list_recoverable_backups(project_key(authorization))
        authorization.revalidate()
        return {"ok": True, "summary": "Verified backups available for the selected project.", "backups": backups, "project_path": str(authorization.canonical_path)}

    raise FastAPIHTTPException(status_code=400, detail="Unsupported agent tool.")


@router.post("/analyze", response_model=AnalyzeResponse)
async def ai_analyze(request: AnalyzeRequest):
    """Analyze a project with AI."""
    try:
        authorization = authorize_project_path(request.project_path, request.access_grant_id)
    except ProjectAccessError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    path = authorization.canonical_path
    
    # First, run deterministic scan
    analysis = analyze_project(path)
    try:
        authorization.revalidate()
    except ProjectAccessError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    
    # Build structured candidate context for Nemotron
    candidate_context = []
    for c in analysis.cleanup_candidates:
        candidate_context.append({
            "path": c.path,
            "size_bytes": c.size_bytes,
            "scanner_risk": c.risk.value,
            "scanner_reason": c.reason,
        })
    
    # Call the configured provider. Configuration errors must not turn into demo success.
    try:
        provider = get_ai_provider()
    except Exception as e:
        logging.getLogger(__name__).error("AI provider initialization failed: %s", type(e).__name__)
        raise HTTPException(status_code=503, detail="Nebius provider configuration failed. Check backend configuration.") from e
    from ai.provider import ChatMessage as ProviderChatMessage
    
    # Create structured prompt for Nemotron
    system_prompt = """You are DevSweep AI, analyzing developer workspace cleanup candidates.
You receive deterministic scanner findings and must provide structured recommendations.

For each candidate, respond with:
- path: the exact path from the scanner
- action: "DELETE" or "KEEP"
- risk: "SAFE", "CAUTION", or "DANGEROUS" 
- reason: concise explanation

Rules:
1. Never recommend DANGEROUS items for deletion
2. If scanner says SAFE but you see risk, upgrade to CAUTION (never downgrade)
3. Only recommend paths that were in the scanner results
4. Return valid JSON only"""
    
    user_prompt = f"""Project Analysis:
- Path: {path}
- Type: {analysis.project_type.value}
- Framework: {analysis.framework}
- Package Manager: {analysis.package_manager}
- Language: {analysis.language}
- Git: {analysis.has_git} (clean: {analysis.git_clean})

Scanner Candidates ({len(candidate_context)} items):
{json.dumps(candidate_context, indent=2)}

Return JSON:
{{
  "recommendations": [
    {{"path": "...", "action": "DELETE|KEEP", "risk": "SAFE|CAUTION|DANGEROUS", "reason": "..."}}
  ]
}}"""
    
    messages = [
        ProviderChatMessage(role="system", content=system_prompt),
        ProviderChatMessage(role="user", content=user_prompt),
    ]

    ai_recommendations = []
    ai_used = False
    try:
            response = await provider.structured_completion(
                messages=messages,
                response_schema={
                    "type": "object",
                    "properties": {
                        "recommendations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "path": {"type": "string"},
                                    "action": {"type": "string", "enum": ["DELETE", "KEEP"]},
                                    "risk": {"type": "string", "enum": ["SAFE", "CAUTION", "DANGEROUS"]},
                                    "reason": {"type": "string"},
                                },
                                "required": ["path", "action", "risk", "reason"],
                            },
                        },
                    },
                    "required": ["recommendations"],
                },
            )
            ai_recommendations = response.get("recommendations", [])
    except Exception as e:
        # Log the sanitized error
        logging.getLogger(__name__).warning("AI structured_completion failed: %s", type(e).__name__)
        # Re-raise to surface the failure - do not silently fall back
        error_type = type(e).__name__
        if error_type in {"AuthenticationError", "PermissionDeniedError"}:
            raise HTTPException(status_code=502, detail="Nebius authentication failed. Verify backend credentials.") from e
        if error_type == "RateLimitError":
            raise HTTPException(status_code=429, detail="Nebius rate limit reached. Retry later.") from e
        raise HTTPException(status_code=502, detail=f"Nebius inference failed: {error_type}") from e

    ai_used = isinstance(provider, NebiusProvider) and not settings.DEVSWEEP_DEMO_MODE

    # Merge AI recommendations with scanner results (safety validation)
    # Only use AI recommendations for paths that exist in scanner results
    scanner_paths = {c.path: c for c in analysis.cleanup_candidates}
    final_candidates = []
    
    for ai_rec in ai_recommendations:
        path = ai_rec.get("path", "")
        if path not in scanner_paths:
            # Reject unknown paths
            continue
        
        scanner_candidate = scanner_paths[path]
        
        # Scanner risk remains authoritative for validation
        scanner_risk = scanner_candidate.risk.value
        ai_risk = ai_rec.get("risk", "SAFE")
        
        # Reject DANGEROUS deletions based on scanner risk
        action = ai_rec.get("action", "KEEP")
        if scanner_risk == "DANGEROUS" and action == "DELETE":
            action = "KEEP"
        
        final_candidates.append({
            "path": path,
            "risk": scanner_risk,  # Deterministic scanner risk (authoritative for validation)
            "ai_risk": ai_risk,    # AI-assessed risk (can be higher, used for approval)
            "reason": ai_rec.get("reason", scanner_candidate.reason),
            "size_bytes": scanner_candidate.size_bytes,
            "size_human": format_bytes(scanner_candidate.size_bytes),
            "action": action,
        })
    
    total_recoverable = sum(c["size_bytes"] for c in final_candidates if c["action"] == "DELETE" and c["risk"] in ("SAFE", "CAUTION"))

    try:
        authorization.revalidate()
    except ProjectAccessError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc

    analysis_id = None
    if ai_used:
        if len(_verified_analyses) >= 256:
            _verified_analyses.pop(next(iter(_verified_analyses)))
        analysis_id = str(uuid.uuid4())
        _verified_analyses[analysis_id] = {
            "project_path": str(path),
            "authorization": authorization,
            "candidates": final_candidates,
            "expires_at": time.monotonic() + VERIFIED_ANALYSIS_TTL_SECONDS,
        }

    return AnalyzeResponse(
        project_type=analysis.project_type.value,
        framework=analysis.framework,
        package_manager=analysis.package_manager,
        language=analysis.language,
        candidates=final_candidates,
        total_recoverable=total_recoverable,
        total_recoverable_human=format_bytes(total_recoverable),
        ai_used=ai_used,
        provider_name=provider.provider_name,
        model=provider.model_name,
        demo_mode=settings.DEVSWEEP_DEMO_MODE,
        analysis_id=analysis_id,
    )


@router.get("/models")
async def get_models():
    """Get available AI models."""
    try:
        provider = get_ai_provider()
    except Exception as e:
        logging.getLogger(__name__).error("AI provider initialization failed: %s", type(e).__name__)
        raise HTTPException(status_code=503, detail="Nebius provider configuration failed. Check backend configuration.") from e
    return {
        "current": provider.model_name if hasattr(provider, 'model_name') else "unknown",
        "provider": provider.__class__.__name__,
        "provider_name": provider.provider_name,
        "model": provider.model_name,
        "demo_mode": settings.DEVSWEEP_DEMO_MODE,
        "real_inference_available": provider.provider_name != "mock" and not settings.DEVSWEEP_DEMO_MODE,
    }
