"""REUSABLE DECISION PATTERN: tool selection for a laptop recommendation agent  (#tool-selection)

What it does
    Before the LLM responds to a laptop query, Strands Decider 2B reads the user's message and
    picks exactly which tool should handle it:
    - is it a search by use case / budget? → search_laptops
    - is it a side-by-side comparison of two models? → compare_laptops
    - is it a price filter ("under $X")? → filter_by_budget
    - is it a request for full specs on one model? → get_laptop_details
    - can it be answered directly without a tool? → none
    When the decider is unsure (confidence below threshold), all tools are kept and the LLM
    chooses, so no information is lost.

Typed questions and options
    `tool` (choice): one option per tool (described by its docstring) plus `none`.
    Options are derived at runtime from the tools list — adding a tool needs no retraining.

Wiring
    `LaptopToolSelector` wraps `ToolSelector` from `decider_kit.patterns.tool_selection`.
    `agent/agent.py` calls `selector.tools_for(message)` to get the narrowed tool list, then
    passes it to the Strands Agent so the LLM sees only the relevant tool in context:

        selector = LaptopToolSelector(decider)
        agent = Agent(model=..., tools=selector.tools_for(user_message), ...)

How to reuse it
    Copy this file. Replace `TOOLS` with your own @tool functions, each with a clear one-line
    docstring. Adjust `THRESHOLD` if you want the decider to be more or less conservative.
    The `ToolSelector` class is generic — it reads the docstrings at runtime, so no question
    list needs updating when tools change.
"""

from __future__ import annotations

from decider_kit import Decider
from decider_kit.patterns.tool_selection import ToolSelector, questions_for

from .tools import TOOLS

PATTERN_TAG = "#tool-selection"

# Build QUESTIONS from the live tool list so the benchmark can run without an agent instance.
QUESTIONS = questions_for(TOOLS)

# Confidence threshold: below this the full tool list is kept and the LLM decides.
THRESHOLD = 0.60


class LaptopToolSelector:
    """Wraps ToolSelector for the laptop advisor. Keeps a log of every decision."""

    def __init__(self, decider: Decider | None = None):
        self.decider = decider or Decider()
        self._selector = ToolSelector(self.decider, TOOLS, threshold=THRESHOLD,
                                      context="for a laptop recommendation assistant")
        self.log: list[dict] = []

    def tools_for(self, message: str, history: str = "") -> list:
        """Return the narrowed tool list for this message (or all tools if unsure)."""
        tools = self._selector.tools_for(message, history)
        # Copy the latest selector log entry into our log with the pattern tag
        if self._selector.log:
            entry = dict(self._selector.log[-1])
            entry["pattern"] = PATTERN_TAG
            self.log.append(entry)
        return tools

    def flush_log(self, since: int = 0) -> list[dict]:
        """Return log entries added since position `since`."""
        return self.log[since:]
