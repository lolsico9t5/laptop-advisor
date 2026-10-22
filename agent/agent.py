"""LaptopAdvisor: an LLM does the talking, Strands Decider 2B picks the tool.

    from agent.agent import HackathonAgent
    out = HackathonAgent().chat("I need a laptop for video editing under $2000")
    out["reply"], out["decisions"]

The interface (`HackathonAgent.chat`) is the same as the kit contract, so the demo UI,
the benchmark, the video and the AWS deployment all work unchanged.
"""

from __future__ import annotations

import time
from typing import Any

from strands import Agent

from decider_kit import Decider
from decider_kit.llm import agent_model, default_model_id, image_blocks, strip_thinking

from .decision import LaptopToolSelector
from .tools import TOOLS

NAME = "LaptopAdvisor"

SYSTEM_PROMPT = """You are LaptopAdvisor, a friendly and knowledgeable assistant that helps people choose the right laptop.

You have access to a catalog of 30 laptops covering all budgets, use cases and brands.

When a user describes what they need:
1. Use the available tools to find relevant options.
2. Recommend the best 1–3 laptops with clear reasons why each fits their needs.
3. Mention trade-offs honestly (battery life, weight, price, OS).
4. Ask a clarifying question if the budget or use case is unclear.

Be concise, warm and practical. Never invent specs — only use what the tools return."""


class HackathonAgent:
    """One Strands agent per session. Strands Decider 2B narrows the tool list before each turn."""

    def __init__(self, decider: Decider | None = None, model_id: str | None = None, eager: bool | None = None):
        import os

        self.decider = decider or Decider()
        self.model_id = model_id or default_model_id()
        # `eager` is accepted for demo compatibility but not used — the agent always asks naturally
        self.eager = eager if eager is not None else False
        self.sessions: dict[str, dict[str, Any]] = {}

    def _session(self, session_id: str) -> dict[str, Any]:
        if session_id not in self.sessions:
            selector = LaptopToolSelector(self.decider)
            # Agent is rebuilt each turn with a narrowed tool list; we keep the conversation
            # history separately and pass it to the selector for context-aware tool selection.
            self.sessions[session_id] = {"selector": selector, "history": []}
        return self.sessions[session_id]

    def chat(self, message: str, session_id: str = "default", images: list[Any] | None = None) -> dict[str, Any]:
        """Send a message and get a reply with the decisions Strands Decider 2B made."""
        sess = self._session(session_id)
        selector: LaptopToolSelector = sess["selector"]
        history: list[dict] = sess["history"]

        # Build a short text summary of recent history for the selector
        history_text = "\n".join(
            f"{turn['role']}: {turn['content']}" for turn in history[-6:]
        )

        before = len(selector.log)

        # Ask Strands Decider 2B which tool fits this message
        narrowed_tools = selector.tools_for(message, history=history_text)

        t0 = time.perf_counter()

        # Build a fresh agent with the narrowed tool list (keeps context lean)
        agent = Agent(
            model=agent_model(self.model_id),
            system_prompt=SYSTEM_PROMPT,
            tools=narrowed_tools if narrowed_tools else TOOLS,
            callback_handler=None,
        )

        # Replay history as a primed conversation so the agent remembers context
        for turn in history[-10:]:
            agent.messages.append({"role": turn["role"], "content": [{"text": turn["content"]}]})

        content = ([*image_blocks(images), {"text": message}] if images else message)
        result = agent(content, invocation_state={"images": list(images or [])})
        reply = strip_thinking(str(result))

        # Update history
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": reply})

        decisions = selector.flush_log(since=before)

        return {
            "reply": reply,
            "decisions": decisions,
            "model_id": self.model_id,
            "latency_ms": round((time.perf_counter() - t0) * 1000),
            "agent": NAME,
            "eager": self.eager,
        }


if __name__ == "__main__":
    import json
    import sys

    a = HackathonAgent()
    queries = sys.argv[1:] or [
        "I need a laptop for university, budget is $800",
        "Compare the MacBook Air 15 M3 and the Dell XPS 15 OLED",
        "What laptops are under $500?",
        "Tell me everything about the LG Gram 17 2024",
    ]
    for msg in queries:
        print(f"\n>>> {msg}")
        out = a.chat(msg)
        print(out["reply"])
        if out["decisions"]:
            d = out["decisions"][0]
            print(f"[Decider: tool={d.get('tool')} confidence={d.get('confidence')} narrowed={d.get('narrowed')} {d.get('decider_ms')}ms]")
