# LaptopAdvisor: How Strands Decider 2B Makes a Laptop Recommendation Agent Faster and Smarter

## The Problem

Buying a laptop is overwhelming. There are hundreds of models across every price range, and the
right choice depends on what you actually do — gaming, video editing, university work, software
development, or just browsing the web. Most people end up reading a dozen reviews and still feel
unsure.

LaptopAdvisor solves this by letting you describe your needs in plain language and returning a
clear, reasoned recommendation. You say "I need something for university on a tight budget" and
it finds the best matches, explains the trade-offs, and answers follow-up questions naturally.

## The Agent

LaptopAdvisor is a conversational agent built with the Strands Agents SDK and deployed on
Amazon Bedrock AgentCore Runtime. It uses Amazon Nova Pro (via Amazon Bedrock) for the
conversation and reasoning, and a catalog of 30 laptops covering all budgets, use cases and
brands for its data.

The agent has four tools:

| Tool | What it does |
|---|---|
| `search_laptops` | Finds matching laptops by use case and optional budget |
| `compare_laptops` | Side-by-side spec comparison of two named models |
| `filter_by_budget` | Lists all laptops available within a maximum price |
| `get_laptop_details` | Full specifications and review summary for one model |

Every user message maps naturally to one of these tools — or to none of them (a greeting, a
general question). The challenge is routing each message to the right tool quickly and cheaply,
without always asking the LLM to decide.

## The Decision: Tool Selection with Strands Decider 2B

Before the LLM sees each user message, Strands Decider 2B reads it and answers one question:

> **Which tool should handle this request?**
> Options: `search_laptops`, `compare_laptops`, `filter_by_budget`, `get_laptop_details`, `none`

Each option is described by the tool's own docstring, so no retraining is needed when a tool
changes. The decider returns a confidence score alongside its answer. If confidence is above
0.60, the agent gets only that one tool in its context — the LLM focuses on reasoning and
explaining rather than routing. If the decider is unsure, all tools are kept and the LLM
chooses, so nothing is ever lost.

This is the `#tool-selection` pattern from the `decider_kit` library.

```python
# agent/decision.py (reusable pattern)
selector = LaptopToolSelector(decider)
narrowed_tools = selector.tools_for(user_message)   # one tool, or all four if unsure
agent = Agent(model=..., tools=narrowed_tools, ...)
agent(user_message)
```

## Measured Results

Benchmarked on 15 held-out test cases covering all four tools and direct answers:

| | Strands Decider 2B | LLM (qwen3.5-4b) |
|---|---|---|
| Accuracy | 80.0% | 86.7% |
| Latency p50 per decision | 1,794 ms | 9,830 ms |
| Latency p95 | 1,960 ms | 9,966 ms |
| Cost per 1,000 decisions | $0.035 | $0.00 (ugmdu cloud) |
| Confident answers (≥ 0.70) | 53% | 100% |
| Accuracy when confident | **100%** | 86.7% |
| Median speedup | **5.5×** | — |

**The decider is 5.5× faster at the median.** When it answers confidently (53% of cases), it is
100% accurate — better than the LLM baseline of 86.7%. For the remaining 47% where confidence
is below threshold, the fallback to the full tool list means the LLM still gets it right.

**Where the decider struggles:** `filter_by_budget` vs `search_laptops` are the hardest to
distinguish — a message like "what laptops are under $500?" sits on the boundary between the
two, and the decider often assigns moderate confidence to both. This is expected: the semantic
overlap is real, and the safe fallback (keep all tools) handles it correctly.

## Why a Decision Model Here

The check runs on every single user message. Over many conversations the latency and cost
savings add up significantly. More importantly, a narrowed tool list gives the LLM a cleaner
context — it can focus its reasoning on explaining the recommendation rather than deciding
which function to call. In live testing, responses with a narrowed tool list were more
focused and used fewer tokens.

A guardrail or policy check written as a prompt would cost the same as a full LLM turn every
time. Strands Decider 2B does it in under two seconds for $0.035 per thousand decisions.

## Architecture

```
User message
    │
    ▼
Strands Decider 2B  ──►  tool: search_laptops (confidence 0.83)
    │
    ▼
Strands Agent (Amazon Nova Pro via Bedrock)
    │  tools: [search_laptops]   ← narrowed context
    ▼
search_laptops(use_case="gaming", budget=1500)
    │
    ▼
Reply: "Here are the top gaming laptops under $1,500…"
```

When the decider is unsure, the agent gets all four tools and the LLM routes normally — the
decision model degrades gracefully rather than failing.

## The Reusable Decision Pattern

The `#tool-selection` pattern in `agent/decision.py` is generic. To reuse it:

1. Write your tools as Strands `@tool` functions with a clear one-line docstring each.
2. Copy `LaptopToolSelector` and replace `TOOLS` with your tool list.
3. Call `selector.tools_for(user_message)` before building your agent.

The option descriptions are read from the docstrings at runtime — no question list to maintain,
no retraining when tools change.

```python
# How to reuse in your own agent
from decider_kit.patterns.tool_selection import ToolSelector
from decider_kit import Decider

selector = ToolSelector(Decider(), tools=[your_tool_a, your_tool_b, your_tool_c])
narrowed = selector.tools_for(user_message)   # returns subset, or all tools if unsure
agent = Agent(model=..., tools=narrowed, ...)
```

## How to Run It

```bash
git clone https://github.com/<your-username>/laptop-advisor
cd laptop-advisor
pip install -e .
cp .env.example .env   # add your keys
python -m agent.agent "I need a laptop for video editing under $2000"
```

Full setup and deploy instructions are in the README.

## What I Learned

The most interesting finding was the confidence split. The decider is either very sure
(confidence above 0.85, always correct on these cases) or genuinely unsure (confidence around
0.50, where the semantic boundary between tools is ambiguous). There is almost no middle ground.
This makes the threshold simple to set: pick a value between 0.60 and 0.75 and the behaviour
is predictable.

The weak spot — `filter_by_budget` vs `search_laptops` — could be improved by making the tool
docstrings more distinct, or by rephrasing the question to ask "is this a pure price filter or
a use-case search?" as a prior step. This is the kind of tuning that the `--split tune` /
`--split test` separation in the benchmark makes safe to do honestly.

---

*Built with the AWS User Group Madurai Strands Decider hackathon kit.*
