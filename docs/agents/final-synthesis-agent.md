# Final Synthesis Agent

Stage 3 adds a single owner for user-facing final answers:

```text
agents/final_synthesis_agent.py
```

Departments return structured outputs. Final Synthesis merges them into the
final answer and carries forward:

- route decision
- execution plan
- department outputs
- validation evidence
- citations
- limits

Rule:

```text
Departments produce department outputs.
Final Synthesis Agent produces the final answer.
```
