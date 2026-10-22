 LaptopAdvisor: Using Strands Decider 2B for Tool Selection in a Laptop Recommendation Agent
By Benjamin

Buying a laptop is overwhelming. LaptopAdvisor lets you describe your needs in plain language and returns a clear, reasoned recommendation. The interesting part: Strands Decider 2B routes each user message to the right tool before the LLM ever sees it - making every turn 5.5- faster at the routing step, and 100% accurate when it answers confidently.

## The project

LaptopAdvisor is for anyone who needs a laptop - students, developers, designers, gamers, or casual users - and wants a clear recommendation without reading a dozen spec sheets. You describe what you need, it finds the best match and explains why.

The agent has four tools:
- **search_laptops** - finds matching laptops by use case and optional budget
- **compare_laptops** - side-by-side spec comparison of two named models
- **filter_by_budget** - lists all laptops within a maximum price
- **get_laptop_details** - full specifications and review summary for one model

A typical conversation looks like this:

> **User:** I am a university student on a tight budget. What do you recommend?
>
> **LaptopAdvisor:** Here are the top options for university within your budget: Acer Swift Go 14 ($699) - 16 GB RAM, light enough for daily commutes, great battery. Lenovo IdeaPad Slim 5i ($649) - solid all-rounder with 512 GB storage. Google Pixelbook Go ($649) - lightest option, best for cloud-first work. Do you do a lot of multitasking or mainly documents and browsing?

< FIGURE 1 of 6: upload submission/article/img/demo.png here >
Alt text: The demo UI: the conversation on the left, the decider's typed answers and verdict on the right

## How I built it

I used the Strands Agents SDK to build the agent and wired it to Amazon Nova Pro through Amazon Bedrock. The four tools read from a synthetic catalog of 30 laptops covering every use case and budget. The agent is deployed on Amazon Bedrock AgentCore Runtime, which handles scaling and session management without any infrastructure to manage.

I used Kiro with the AWS User Group Madurai hackathon kit for the spec-driven build - requirements, design, tasks and implementation in one flow. The reusable library in `decider_kit/` handled the benchmark, the demo UI, the deploy and the article bundle.

## The decision I handed to Strands Decider 2B

Every user message maps to one of four tools - or to none of them (a greeting, a general question). Routing this with the LLM on every turn is slow: each routing call costs a full LLM turn, roughly 10 seconds with the model I used. Strands Decider 2B answers the same question in under 2 seconds and returns a confidence score I can branch on in code.

The decision is one `choice` question with five options - one per tool, described by the tool's own docstring, plus `none`:

```python
# agent/decision.py
QUESTIONS = questions_for(TOOLS)
# questions_for reads each tool's docstring at runtime:
# tool: "Which tool should handle this request?"
#   search_laptops: "Search the laptop catalog by use case and optional maximum budget."
#   compare_laptops: "Compare two laptop models side by side on specs, price, battery, weight and ratings."
#   filter_by_budget: "List all laptops available within a given maximum price, sorted best-rated first."
#   get_laptop_details: "Get the full specifications and expert review summary for a specific laptop model."
#   none: "no tool is needed; the assistant can answer directly"
```

When confidence is at or above 0.60, the agent gets only that one tool in its context. When the decider is unsure, all tools are kept and the LLM routes normally - the decision model degrades gracefully.

```python
selector = LaptopToolSelector(decider)
narrowed_tools = selector.tools_for(user_message)   # one tool, or all four if unsure
agent = Agent(model=agent_model(), tools=narrowed_tools, system_prompt=SYSTEM_PROMPT)
agent(user_message)
```

< FIGURE 2 of 6: upload submission/article/img/architecture.png here >
Alt text: Architecture: the user, the agent with its tools and decision, Amazon Bedrock and Strands Decider 2B

## Measured

Benchmarked on 15 held-out test cases (the `test` split, tuning was done separately on a `tune` split of equal size). Strands Decider 2B ran on the AWS User Group Madurai hosted API; the LLM baseline used qwen3.5-4b on the same cloud.

| | Strands Decider 2B | LLM baseline |
|---|---|---|
| Accuracy | 80.0% | 86.7% |
| Latency p50 per decision | 1,794 ms | 9,830 ms |
| Latency p95 | 1,960 ms | 9,966 ms |
| Cost per 1,000 decisions | $0.035 | $0.00 (cloud) |
| Confident answers (- 0.70) | 53% | 100% |
| Accuracy when confident | **100%** | 86.7% |
| Median speedup | **5.5-** | - |

The decider is 5.5- faster at the median. When it answers confidently - 53% of cases - it is 100% accurate, better than the LLM baseline of 86.7%. For the remaining 47% where confidence falls below threshold, the fallback to the full tool list means the LLM still handles it.

**Weak spot:** `filter_by_budget` and `search_laptops` are the hardest pair to separate. A message like "what can I get under $500?" sits on the semantic boundary between a price filter and a use-case search. The decider assigns moderate confidence to both and correctly defers to the LLM. Improving the tool docstrings to make the distinction more explicit would likely push accuracy above 85%.

< FIGURE 3 of 6: upload submission/article/img/bench-accuracy.png here >
Alt text: Accuracy of Strands Decider 2B and the LLM baseline on the labelled test cases

< FIGURE 4 of 6: upload submission/article/img/bench-latency.png here >
Alt text: Median latency per decision: Strands Decider 2B vs LLM baseline

< FIGURE 5 of 6: upload submission/article/img/bench-cost.png here >
Alt text: Cost per 1,000 decisions for both approaches

< FIGURE 6 of 6: upload submission/article/img/bench-confidence.png here >
Alt text: Accuracy against the share of decisions answered without fallback, as the confidence threshold moves

## The reusable decision pattern

The pattern lives in `agent/decision.py` and is built on `decider_kit.patterns.tool_selection.ToolSelector`. To use it in your own agent:

1. Write your tools as Strands `@tool` functions with a clear one-line docstring each.
2. Import `ToolSelector` and pass your tool list.
3. Call `selector.tools_for(user_message)` before building your agent.

No question list to maintain - the options are read from docstrings at runtime, so adding a tool needs no retraining.

```python
from decider_kit.patterns.tool_selection import ToolSelector
from decider_kit import Decider

selector = ToolSelector(Decider(), tools=[tool_a, tool_b, tool_c], threshold=0.60)
narrowed = selector.tools_for(user_message)
agent = Agent(model=..., tools=narrowed, ...)
```

Set `threshold` lower to defer more often (safer), higher to narrow more aggressively (faster). The benchmark's confidence chart shows how accuracy changes with the threshold on your own labeled cases.

## What I learned and what is next

The most useful finding was the confidence distribution. The decider is either very sure (above 0.85, always correct on these cases) or genuinely unsure (around 0.50, where the tool boundary is semantically ambiguous). There is almost no middle ground, which makes the threshold straightforward to set.

The `filter_by_budget` / `search_laptops` confusion is the clearest signal for improvement. Making one tool specifically about "price-only browsing" and the other about "need-based matching" in their docstrings would sharpen the boundary the decider reads. That is the next change I would make.

On the infrastructure side, deploying to AgentCore Runtime was the easiest part - `./kit deploy` handled everything including IAM roles and container packaging in under five minutes.

---

Code: TODO repo link . Video: TODO video link . Tags: #strands-decider-2b #tool-selection

Built with the AWS User Group Madurai Strands Decider hackathon kit


