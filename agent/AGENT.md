# Use case

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
