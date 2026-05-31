"""
supervisor.py — Orchestrates the full multi-agent pipeline using LangGraph.

Pipeline:
  github_agent → parser_agent → router_agent → [edge_answer | edge_coding] → END

State flows through each node; every agent's output is merged into the shared
AgentState dict and passed to the next node automatically.
"""

import json
import os
from typing import Annotated, Literal, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage
from langgraph.graph import END, START, StateGraph

# ── Import your existing agents ──────────────────────────────────────────────
from src.github_agent import github_agent
from src.parser_agent import parser_agent
from src.router_agent import router_agent
from src.edge_answer_agent import agent as _edge_answer_agent
from src.edge_coding_executor import run_edge_coding_task

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# Input schema — ONLY these two fields show up in Studio's input panel
# ─────────────────────────────────────────────────────────────────────────────

class InputState(TypedDict):
    repo_url: str    # e.g. https://github.com/your-org/your-repo
    task_text: str   # e.g. "Add docstrings to all functions in utils.py"


# ─────────────────────────────────────────────────────────────────────────────
# Full internal state — all keys, most populated by agents during the run
# ─────────────────────────────────────────────────────────────────────────────

class AgentState(TypedDict, total=False):
    # ── Inputs ────────────────────────────────────────────────────────────────
    repo_url: str          # supplied by the caller
    task_text: str         # user's natural-language task

    # ── github_agent outputs ──────────────────────────────────────────────────
    repo_path: str
    repo_context: str

    # ── parser_agent outputs ──────────────────────────────────────────────────
    parsed_task: dict      # structured JSON from the parser

    # ── router_agent outputs ──────────────────────────────────────────────────
    routing: str           # LOCAL | CLOUD | CONFIRM | BLOCKED
    router_scores: dict    # {privacy, security, complexity, latency, reason}

    # ── edge agent outputs ────────────────────────────────────────────────────
    final_answer: str      # prose answer (edge_answer_agent)
    coding_result: dict    # branch/files/summary (edge_coding_executor)

    # ── human-in-the-loop ────────────────────────────────────────────────────
    user_confirmation: bool | None   # set externally when routing == CONFIRM


# ─────────────────────────────────────────────────────────────────────────────
# Node implementations — each wraps an existing agent
# ─────────────────────────────────────────────────────────────────────────────

def node_github(state: AgentState) -> AgentState:
    """Clone / update the repo and build a context snapshot."""
    result = github_agent(state["repo_url"])
    return {**state, **result}          # repo_path + repo_context injected


def node_parser(state: AgentState) -> AgentState:
    """Turn the raw task + repo context into structured JSON."""
    parsed = parser_agent(
        task_text=state["task_text"],
        repo_context=state["repo_context"],
    )
    return {**state, "parsed_task": parsed}


def node_router(state: AgentState) -> AgentState:
    """Score the task and decide LOCAL / CLOUD / CONFIRM / BLOCKED."""
    prompt = json.dumps(
        {
            "task_summary": state["parsed_task"].get("task_summary", ""),
            "requested_change": state["parsed_task"].get("requested_change", ""),
            "will_modify_repo": state["parsed_task"].get("will_modify_repo", False),
            "will_run_code": state["parsed_task"].get("will_run_code", False),
            "required_capabilities": state["parsed_task"].get("required_capabilities", []),
        },
        indent=2,
    )
    resp = router_agent.invoke({"messages": [HumanMessage(content=prompt)]})
    raw = resp["messages"][-1].content
    scores = json.loads(raw)
    return {
        **state,
        "routing": scores["routing"],
        "router_scores": scores,
    }


def node_edge_answer(state: AgentState) -> AgentState:
    """Handle non-repo tasks with the lightweight edge answer agent."""
    prompt = (
        f"Task: {state['task_text']}\n\n"
        f"Parsed context:\n{json.dumps(state['parsed_task'], indent=2)}"
    )
    resp = _edge_answer_agent.invoke({"messages": [HumanMessage(content=prompt)]})
    answer = resp["messages"][-1].content
    return {**state, "final_answer": answer}


def node_edge_coding(state: AgentState) -> AgentState:
    """Handle repo-change tasks: generate code, commit, push."""
    result = run_edge_coding_task(
        remote_url=state["repo_url"],
        task=state["task_text"],
        language=_infer_language(state["parsed_task"]),
    )
    return {
        **state,
        "coding_result": {
            "branch": result.branch,
            "repo_dir": result.repo_dir,
            "summary": result.summary,
            "written_files": result.written_files,
        },
        "final_answer": (
            f"✅ Changes committed to branch `{result.branch}`.\n\n"
            f"{result.summary}\n\n"
            f"Files modified: {', '.join(result.written_files)}"
        ),
    }


def node_blocked(state: AgentState) -> AgentState:
    """Hard stop — task was flagged as too risky."""
    reason = state.get("router_scores", {}).get("reason", "Security or privacy risk.")
    return {
        **state,
        "final_answer": f"🚫 Task blocked by safety policy.\nReason: {reason}",
    }


def node_confirm(state: AgentState) -> AgentState:
    """
    Pause for human approval.

    In production wire this to an interrupt / human-in-the-loop mechanism.
    Here we check `user_confirmation` in the state:
      - True  → continue (re-enter routing)
      - False → abort
      - None  → print instructions and stop (caller must resume with confirmation)
    """
    confirmed = state.get("user_confirmation")
    reason = state.get("router_scores", {}).get("reason", "")

    if confirmed is True:
        # Re-route now that human approved; treat as LOCAL
        return {**state, "routing": "LOCAL"}

    if confirmed is False:
        return {
            **state,
            "final_answer": "🛑 Task cancelled by user.",
        }

    # confirmed is None → surface the prompt to the caller
    print(
        "\n⚠️  CONFIRMATION REQUIRED\n"
        f"Reason: {reason}\n"
        "Set `user_confirmation=True` in state to proceed, "
        "or `False` to abort.\n"
    )
    return {**state, "final_answer": f"⏸️  Waiting for confirmation.\nReason: {reason}"}


# ─────────────────────────────────────────────────────────────────────────────
# Routing / conditional edges
# ─────────────────────────────────────────────────────────────────────────────

def route_after_router(
    state: AgentState,
) -> Literal["edge_answer", "edge_coding", "blocked", "confirm"]:
    routing = state.get("routing", "CONFIRM")
    will_modify = state.get("parsed_task", {}).get("will_modify_repo", False)

    if routing == "BLOCKED":
        return "blocked"
    if routing == "CONFIRM":
        return "confirm"
    # LOCAL or CLOUD — pick coding vs answer
    if will_modify:
        return "edge_coding"
    return "edge_answer"


def route_after_confirm(
    state: AgentState,
) -> Literal["edge_answer", "edge_coding", "blocked"]:
    """After human confirms (or denies), re-check routing."""
    if state.get("user_confirmation") is False:
        return "blocked"
    will_modify = state.get("parsed_task", {}).get("will_modify_repo", False)
    return "edge_coding" if will_modify else "edge_answer"


# ─────────────────────────────────────────────────────────────────────────────
# Build the graph
# ─────────────────────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    g = StateGraph(AgentState, input=InputState)

    # Nodes
    g.add_node("github",       node_github)
    g.add_node("parser",       node_parser)
    g.add_node("router",       node_router)
    g.add_node("edge_answer",  node_edge_answer)
    g.add_node("edge_coding",  node_edge_coding)
    g.add_node("blocked",      node_blocked)
    g.add_node("confirm",      node_confirm)

    # Linear edges
    g.add_edge(START,    "github")
    g.add_edge("github", "parser")
    g.add_edge("parser", "router")

    # Conditional branch after router
    g.add_conditional_edges(
        "router",
        route_after_router,
        {
            "edge_answer": "edge_answer",
            "edge_coding": "edge_coding",
            "blocked":     "blocked",
            "confirm":     "confirm",
        },
    )

    # Conditional branch after human confirm
    g.add_conditional_edges(
        "confirm",
        route_after_confirm,
        {
            "edge_answer": "edge_answer",
            "edge_coding": "edge_coding",
            "blocked":     "blocked",
        },
    )

    # Terminal edges
    g.add_edge("edge_answer", END)
    g.add_edge("edge_coding", END)
    g.add_edge("blocked",     END)

    return g


# Compiled graph — import this in run.py or FastAPI routes
graph = build_graph().compile()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _infer_language(parsed: dict) -> str:
    caps = " ".join(parsed.get("required_capabilities", [])).lower()
    files = " ".join(parsed.get("files_likely_needed", [])).lower()
    combined = caps + " " + files
    for lang in ("typescript", "javascript", "java", "kotlin", "go", "rust"):
        if lang in combined:
            return lang
    return "python"