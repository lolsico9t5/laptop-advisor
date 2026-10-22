# LaptopAdvisor

**a laptop recommendation agent that asks what you need and finds the best laptop for you.**

An agent on AWS that hands one decision to **Strands Decider 2B** and the conversation to **Amazon Bedrock**. Decision pattern: `#tool-selection`. Tags: `#strands-decider-2b` `#tool-selection`.

- Video: (add the YouTube/Vimeo link)
- Article: (add the AWS Builder Center link)
- Deployed: run `./kit deploy`

## The project

- **Pitch:** a laptop recommendation agent that asks what you need and finds the best laptop for you.
- **Who it is for:** anyone looking to buy a laptop — students, developers, designers, gamers, or casual users — who wants a clear, reasoned recommendation without sifting through spec sheets.
- **Features:**
  - describe your needs in plain language and get a ranked recommendation;
  - search the catalog by use case and budget;
  - compare any two laptop models side-by-side;
  - filter the full catalog by maximum price;
  - get detailed specs and a review summary for any model;
  - Strands Decider 2B picks which tool to call so the LLM focuses on explaining, not routing;
  - deployed on Amazon Bedrock AgentCore Runtime.
- **The decision handed to Strands Decider 2B:** for every user request, which tool should handle it — search by use case, compare two models, filter by budget, or fetch full details? (`#tool-selection`)
- **Why a decision model:** the agent has four tools with overlapping applicability; handing tool routing to a fast, cheap classification model reduces wrong tool calls, trims tokens from the LLM context, and keeps latency low.
- **Amazon Bedrock:** the conversation and natural-language reasoning (Amazon Nova Pro by default).



## How it is built

Strands Agents with Amazon Bedrock for the generative part, the tools in `agent/tools.py`, deployed to Amazon Bedrock AgentCore Runtime, and one decision handed to Strands Decider 2B at a clear seam in the agent's path.

Every Amazon Bedrock model id is set in `.env` (`BEDROCK_MODEL_ID`, and `BEDROCK_SMALL/MEDIUM/LARGE_MODEL_ID` for routing), Amazon Nova by default.



## Reusable decision pattern: tool selection for a laptop recommendation agent  (#tool-selection)

The pattern lives in [`agent/decision.py`](agent/decision.py), labelled `REUSABLE DECISION PATTERN`. It contains the typed questions and their options, the wiring that puts the decision in the agent's path, and a note on how to reuse it:

```text
REUSABLE DECISION PATTERN: tool selection for a laptop recommendation agent  (#tool-selection)

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
```

Typed questions:

```python
QUESTIONS = questions_for(TOOLS)
```

## Measured

Decider: strands-decider-2b-hobson-v19 (ugmdu). 15 labelled cases, 15 decisions.

| | Strands Decider 2B | qwen3.5-4b |
|---|---|---|
| Accuracy | 80.0% | 86.7% |
| Latency p50 per decision | 1794 ms | 9830 ms |
| Latency p95 | 1960 ms | 9966 ms |
| Cost per 1,000 decisions | $0.0350 | $0.0000 |
| Answered alone at confidence >= 0.7 | 53% | 100% |
| Accuracy when confident | 100.0% | 86.7% |

At the median the decider was 5.5x faster than the LLM.

Reproduce with `./kit bench` (cases in `agent/eval_cases.jsonl`; charts in `submission/bench/`).

## Run it

```bash
./kit setup        # checks your machine and AWS, sets up Strands Decider 2B (local model or hosted API)
./kit demo         # web UI at http://localhost:8501
./kit bench        # the decision vs an Amazon Bedrock LLM
./kit deploy       # Amazon Bedrock AgentCore Runtime
```

Requirements: Python 3.10+, AWS credentials with Amazon Bedrock access, and for deploying, Node 20+ with the AgentCore CLI (`./kit agentcore-cli`).

## Credits

Built with the AWS User Group Madurai Strands Decider hackathon kit (https://github.com/awsugmdu). The kit's reusable library (`decider_kit/`, the demo UI, the video and article tooling, and the Kiro steering, skills and hooks) is the user group's; the agent in `agent/` is mine. Strands Decider: https://github.com/strands-labs/strands-decider (Apache-2.0).

Licence: Apache-2.0 (see LICENSE).
