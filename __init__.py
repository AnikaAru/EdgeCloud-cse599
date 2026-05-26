"""EdgeCloud-cse599 package.

This repo defines multiple agents with different contracts:

- edge_answer_agent: returns a plain-text response (no repo changes)
- edge_coding_agent: returns a JSON bundle describing repo file changes

The router/orchestrator (implemented elsewhere) should decide which agent to call.
"""

from .edge_answer_agent import agent as edge_answer_agent  # noqa: F401
from .edge_coding_agent import agent as edge_repo_change_agent  # noqa: F401
