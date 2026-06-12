# Business Analyst Agent

Business Analyst Agent is the prompt-only requirement gate before Planner.

It owns:

- problem framing
- fact / inference / assumption / open-question separation
- stakeholder mapping
- scope control
- requirement decomposition
- user stories and pass/fail acceptance criteria
- Planner handoff readiness

It does not own:

- code implementation
- technical stack decisions
- tool calls
- web browsing
- repo inspection
- validation execution

Runtime shape:

```text
Research Agent -> Business Analyst Agent -> Planner Agent
```

The role config lives in `config/roles/business_analyst.yaml`.

The deterministic department runtime lives in `agents/business_analyst_agent.py`.

The prompt/test dataset lives in `business_prompt_lab/ba_agent_eval_v0_1.jsonl`.

Smoke check:

```powershell
python run_ba_agent_smoke.py
```
