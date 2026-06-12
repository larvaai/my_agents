# No-Code Agent Room Flow

This flow is for questions where agents should talk, delegate, review, and synthesize without generating code.

## Roles

- `coordinator`: reads the user question, creates a task board, and assigns specialist agents.
- `context_analyst`: clarifies decision target, constraints, facts, assumptions, and unknowns.
- `market_analyst`: analyzes customer segments, alternatives, positioning, and adoption friction.
- `finance_strategist`: analyzes pricing, ROI proof, resource tradeoffs, and success metrics when relevant.
- `operator`: turns the analysis into workflow, owners, milestones, and validation steps.
- `customer_voice`: represents buyer/user pain, objections, proof needed, and support impact.
- `risk_reviewer`: challenges weak assumptions and may delegate follow-up tasks.
- `final_synthesis`: produces the final answer for the user.

## Conversation Loop

1. User asks one question.
2. Coordinator creates a JSON task board with 3 to 6 tasks.
3. Coordinator delegates tasks to specialist agents.
4. Specialists return structured no-code notes.
5. Review Agent checks gaps, risks, weak evidence, and may assign up to 2 follow-up tasks.
6. Follow-up agents answer the reviewer.
7. Final Synthesis Agent writes one concise answer in the user's language.
8. The run writes `final.md`, `transcript.md`, and `transcript.json` under `var/business_prompt_lab/agent_room/<timestamp>/`.

## No-Code Contract

Agents must not produce:

- source code
- pseudocode
- shell commands
- diffs
- file trees
- implementation snippets
- markdown code fences

If the user asks for code, the room converts the request into requirements, workflow, acceptance criteria, risks, or next actions.

## Run

Mock mode, no LLM call:

```powershell
python .\business_prompt_lab\agent_room.py "Thiet ke luong agent tu giao viec de tra loi cau hoi business" --mock
```

Dry run, only show roster and fallback task board:

```powershell
python .\business_prompt_lab\agent_room.py "Co nen launch add-on reconciliation khong?" --dry-run
```

Real LLM run:

```powershell
python .\business_prompt_lab\agent_room.py "Toi nen validate y tuong SaaS nay nhu the nao?"
```

Interactive:

```powershell
python .\business_prompt_lab\agent_room.py --interactive
```

PowerShell wrapper:

```powershell
.\business_prompt_lab\talk.ps1 "Toi nen uu tien go-to-market hay product discovery?"
```
