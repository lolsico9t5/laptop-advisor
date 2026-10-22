0. LaptopAdvisor helps anyone find the right laptop by understanding their needs in plain language. The agent runs on Amazon Bedrock. Strands Decider picks which tool to call for each request — search, compare, filter or detail — before the LLM responds.

1. A conversational laptop recommendation agent powered by Amazon Bedrock and Strands Decider. What it does: Describe your needs in plain language — budget, use case, preferences. Strands Decider picks the right tool before the LLM responds. Search by use case, compare two models, filter by price, or get full specs. Honest trade-offs: battery, weight, price and OS explained clearly.

2. The agent you are about to see is running on Amazon Bedrock AgentCore Runtime.

3. A student describes their situation in plain language. The decider picks search_laptops. The decider scored confidence 0.83, so the verdict was decided, in 1.1 seconds.

4. The user names two specific models. The decider picks compare_laptops. The decider scored confidence 0.82, so the verdict was decided, in 2.5 seconds.

5. A price-only question. The decider picks filter_by_budget. The decider scored confidence 0.53, so the verdict was decided, in 5.2 seconds.

6. The user wants full details on one model. The decider picks get_laptop_details. The decider scored confidence 0.67, so the verdict was decided, in 7.2 seconds.

7. On 15 labelled decisions, with the decider on the AWS User Group Madurai hosted API, Strands Decider was 80% accurate at a median of 1794 milliseconds, against 87% and 9830 milliseconds for a hosted open LLM asked the same questions.

8. One forward pass per user message. Strands Decider routes each request to the right tool with a typed confidence score the code can act on — faster and cheaper than asking the LLM to decide.