1/
I let a made-up rumor spread through 64 simulated people. Each decides whether to believe it, share it, and how to rewrite it.

"The pool will stay closed this summer because a water test found a problem" became, 6 forwards later, "staff just confirmed... shuttered for good."

[image: 1_arbol.png]

2/
A decision model (Jev, by TypeSafe) gives the odds of believing, sharing and each edit type. An LLM writes the text.

People share what they doubt: 12% believe, 21% share. A fixed logistic rule: 39% believe, and it escalates. With Jev, softening is as common as exaggerating.

[image: 2_resumen.png]

3/
Caveats: Jev is closed and trained on synthetic data, so this shows what a model assumes about people, not how people behave. 64 nodes, 2 messages, 20 seeds each.

80 runs cost $0.13 and replay from cache with no API calls. Code and interactive page: [link]

[image: 3_red_y_linaje.png]
