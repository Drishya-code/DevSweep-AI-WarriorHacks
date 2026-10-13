import asyncio
import json

import pytest
from fastapi.testclient import TestClient

from ai.nebius_provider import NebiusProvider
from ai.provider import AIResponse
from config import settings
from main import app
from persistence.database import persistence
from security.workspace_access import external_project_grants


class ScriptedNebiusProvider(NebiusProvider):
    """OpenAI-compatible provider stub; never connects to Nebius."""

    def __init__(self, responses):
        self._model = "test-nemotron"
        self.responses = list(responses)
        self.calls = []
        self.structured_calls = 0

    async def chat_completion(self, messages, tools=None, tool_choice=None, temperature=0.1, max_tokens=4096):
        self.calls.append({"messages": list(messages), "tools": tools, "tool_choice": tool_choice})
        return self.responses.pop(0)

    async def structured_completion(self, messages, response_schema, temperature=0.1, max_tokens=4096):
        self.structured_calls += 1
        return {"recommendations": [{
            "path": "node_modules", "action": "DELETE", "risk": "SAFE",
            "reason": "Regenerable dependencies.",
        }]}


@pytest.fixture
def agent_environment(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "DEVSWEEP_WORKSPACE_ROOT", str(tmp_path / "allowed"))
    monkeypatch.setattr(settings, "DEVSWEEP_DB_PATH", str(tmp_path / "agent-tests.db"))
    monkeypatch.setattr(settings, "DEVSWEEP_BACKUP_ROOT", str(tmp_path / "backups"))
    monkeypatch.setattr(settings, "DEVSWEEP_DEMO_MODE", False)
    (tmp_path / "allowed" / "sample").mkdir(parents=True)
    (tmp_path / "allowed" / "sample" / "package.json").write_text('{"name":"sample"}', encoding="utf-8")
    (tmp_path / "allowed" / "sample" / "node_modules").mkdir()
    (tmp_path / "allowed" / "sample" / "node_modules" / "placeholder.js").write_text("synthetic", encoding="utf-8")
    import ai.routes as ai_routes
    from cleanup.routes import _cleanup_plans, _pre_cleanup_snapshots
    ai_routes._verified_analyses.clear()
    _cleanup_plans.clear()
    _pre_cleanup_snapshots.clear()
    external_project_grants.clear()
    yield tmp_path / "allowed" / "sample"
    ai_routes._verified_analyses.clear()
    _cleanup_plans.clear()
    _pre_cleanup_snapshots.clear()
    external_project_grants.clear()
    asyncio.run(persistence.close())


def _tool(name, arguments, call_id="call-1"):
    return {"id": call_id, "type": "function", "function": {"name": name, "arguments": arguments}}


def _chat(client, project, message="Scan my project", **extra):
    return client.post("/api/ai/chat", json={"message": message, "project_path": str(project), **extra})


def test_mock_intent_distinguishes_scan_opportunities_from_plan_requests():
    from ai.routes import _extract_requested_path, _intent_tool
    assert _intent_tool("Scan my current workspace for cleanup opportunities.") == "devsweep_scan_workspace"
    assert _intent_tool("Create a cleanup plan for my project.") == "devsweep_plan_cleanup"
    assert _intent_tool("What can I safely remove from my project?") == "devsweep_scan_workspace"
    assert _extract_requested_path(r"Scan D:\Projects\does-not-exist.") == r"D:\Projects\does-not-exist"


def test_scan_tool_executes_and_returns_actual_results_to_model(agent_environment, monkeypatch):
    import ai.routes as ai_routes
    provider = ScriptedNebiusProvider([
        AIResponse(content="", tool_calls=[_tool("devsweep_scan_workspace", "{}")]),
        AIResponse(content="The scan found the synthetic node_modules candidate. Nothing was deleted."),
    ])
    monkeypatch.setattr(ai_routes, "get_ai_provider", lambda: provider)

    response = _chat(TestClient(app), agent_environment)

    assert response.status_code == 200, response.text
    data = response.json()
    assert data["workspace"]["project_path"] == str(agent_environment)
    assert any(item["path"] == "node_modules" for item in data["workspace"]["cleanup_candidates"])
    assert data["response"].startswith("The scan found")
    assert provider.calls[0]["tool_choice"] == "auto"
    assert any(message.role == "tool" and "node_modules" in message.content for message in provider.calls[1]["messages"])
    assert not any("access_grant_id" in message.content for message in provider.calls[1]["messages"])


def test_raw_json_tool_envelope_is_dispatched_and_never_returned_as_plain_answer(agent_environment, monkeypatch):
    import ai.routes as ai_routes
    provider = ScriptedNebiusProvider([
        AIResponse(content='{"tool":"devsweep_scan_workspace","arguments":{}}'),
        AIResponse(content="I scanned the selected project and returned the real findings."),
    ])
    monkeypatch.setattr(ai_routes, "get_ai_provider", lambda: provider)

    response = _chat(TestClient(app), agent_environment)

    assert response.status_code == 200
    assert response.json()["response"] == "I scanned the selected project and returned the real findings."
    assert response.json()["workspace"]["project_path"] == str(agent_environment)


def test_plan_tool_uses_live_scoped_analysis_and_returns_review_only_plan(agent_environment, monkeypatch):
    import ai.routes as ai_routes
    from cleanup.routes import _cleanup_plans
    provider = ScriptedNebiusProvider([
        AIResponse(content="", tool_calls=[_tool("devsweep_plan_cleanup", "{}")]),
        AIResponse(content="I created a plan for review. Nothing was deleted."),
    ])
    monkeypatch.setattr(ai_routes, "get_ai_provider", lambda: provider)

    response = _chat(TestClient(app), agent_environment, "Create a cleanup plan for my current project")

    assert response.status_code == 200, response.text
    data = response.json()
    assert provider.structured_calls == 1
    assert data["plan"]["plan_id"] in _cleanup_plans
    assert data["plan"]["items"][0]["path"] == "node_modules"
    assert data["plan"]["requires_approval"] is False
    assert "execute" not in {tool["function"]["name"] for tool in provider.calls[0]["tools"]}
    assert _cleanup_plans[data["plan"]["plan_id"]]["execution_id"] is None


def test_unknown_execute_tool_is_rejected_without_running_cleanup(agent_environment, monkeypatch):
    import ai.routes as ai_routes
    provider = ScriptedNebiusProvider([
        AIResponse(content="", tool_calls=[_tool("devsweep_execute_cleanup", "{}")]),
        AIResponse(content="I cannot execute cleanup from chat. Review a plan in Cleanup Plans."),
    ])
    monkeypatch.setattr(ai_routes, "get_ai_provider", lambda: provider)

    response = _chat(TestClient(app), agent_environment, "Clean this now")

    assert response.status_code == 200
    result = response.json()["tool_results"][0]
    assert result["ok"] is False
    assert "Unsupported tool" in result["summary"]
    assert "execute_cleanup" not in response.json()["response"]


def test_duplicate_tool_calls_reuse_result_and_malformed_arguments_are_safe(agent_environment, monkeypatch):
    import ai.routes as ai_routes
    provider = ScriptedNebiusProvider([
        AIResponse(content="", tool_calls=[
            _tool("devsweep_scan_workspace", "{}", "call-1"),
            _tool("devsweep_scan_workspace", "{}", "call-2"),
            _tool("devsweep_scan_workspace", "not-json", "call-3"),
        ]),
        AIResponse(content="I completed one scan; a duplicate reused the result, and malformed arguments were rejected."),
    ])
    monkeypatch.setattr(ai_routes, "get_ai_provider", lambda: provider)

    response = _chat(TestClient(app), agent_environment)

    assert response.status_code == 200
    results = response.json()["tool_results"]
    assert results[0]["workspace"]["scan_id"] == results[1]["workspace"]["scan_id"]
    assert results[2]["ok"] is False
    assert results[2]["summary"].startswith("Expecting value")


def test_invalid_requested_path_never_falls_back_to_selected_project(agent_environment, monkeypatch):
    import ai.routes as ai_routes
    missing_path = str(agent_environment.parent / "does-not-exist")
    provider = ScriptedNebiusProvider([
        AIResponse(content="", tool_calls=[_tool("devsweep_scan_workspace", json.dumps({"path": missing_path}))]),
        AIResponse(content="The requested path is unavailable. I did not scan another project."),
    ])
    monkeypatch.setattr(ai_routes, "get_ai_provider", lambda: provider)

    response = _chat(TestClient(app), agent_environment, f"Scan {missing_path}")

    assert response.status_code == 200
    assert response.json()["workspace"] is None
    assert "unavailable" in response.json()["tool_results"][0]["summary"].lower()
    tool_message = next(message for message in provider.calls[1]["messages"] if message.role == "tool")
    assert "unavailable" in tool_message.content.lower()
    assert response.json()["tool_results"][0].get("workspace") is None


def test_external_path_without_explicit_grant_is_rejected(agent_environment, tmp_path, monkeypatch):
    import ai.routes as ai_routes
    outside = tmp_path / "outside" / "sample"
    outside.mkdir(parents=True)
    provider = ScriptedNebiusProvider([
        AIResponse(content="", tool_calls=[_tool("devsweep_scan_workspace", json.dumps({"path": str(outside)}))]),
        AIResponse(content="That folder needs an explicit workspace grant."),
    ])
    monkeypatch.setattr(ai_routes, "get_ai_provider", lambda: provider)

    response = _chat(TestClient(app), agent_environment, f"Scan {outside}")

    assert response.status_code == 200
    assert response.json()["workspace"] is None
    assert "explicit folder registration" in response.json()["tool_results"][0]["summary"]


def test_no_selected_project_and_empty_tool_arguments_use_configured_workspace(agent_environment, monkeypatch):
    import ai.routes as ai_routes
    provider = ScriptedNebiusProvider([
        AIResponse(content="", tool_calls=[_tool("devsweep_scan_workspace", "{}")]),
        AIResponse(content="Please select a project or provide its absolute folder path."),
    ])
    monkeypatch.setattr(ai_routes, "get_ai_provider", lambda: provider)

    response = TestClient(app).post("/api/ai/chat", json={"message": "Scan my current workspace"})

    assert response.status_code == 200
    assert response.json()["workspace"]["project_path"] == str(agent_environment.parent)
    assert response.json()["tool_results"][0]["ok"] is True


def test_mock_provider_rejects_explicit_invalid_path_without_scanning_selected_project(agent_environment, monkeypatch):
    import ai.routes as ai_routes
    from ai.provider import MockProvider
    monkeypatch.setattr(ai_routes, "get_ai_provider", lambda: MockProvider())

    missing = str(agent_environment.parent / "does-not-exist")
    response = _chat(TestClient(app), agent_environment, f"Scan {missing}.")

    assert response.status_code == 200
    data = response.json()
    assert data["workspace"] is None
    assert data["tool_results"][0]["ok"] is False
    assert "unavailable" in data["response"].lower()


def test_analysis_token_from_one_workspace_cannot_authorize_another(agent_environment, tmp_path, monkeypatch):
    import time
    import ai.routes as ai_routes
    from security.workspace_access import authorize_project_path

    other = agent_environment.parent / "different-project"
    other.mkdir()
    first_auth = authorize_project_path(str(agent_environment))
    second_auth = authorize_project_path(str(other))
    ai_routes._verified_analyses["workspace-bound-analysis"] = {
        "authorization": first_auth,
        "expires_at": time.monotonic() + 60,
        "candidates": [],
    }
    assert ai_routes.take_verified_analysis("workspace-bound-analysis", second_auth) is None
