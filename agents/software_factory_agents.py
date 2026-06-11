from __future__ import annotations

import ast
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agents.artifact_protocol import (
    ArtifactRef,
    StageResult,
    brief_text,
    read_artifact_text,
    stage_blocked,
    stable_json,
    write_json_artifact,
    write_text_artifact,
)


def _normalize_path(value: str) -> str:
    return value.replace("\\", "/").strip().strip("`'\"")


def extract_requested_files(task: str) -> list[str]:
    project = infer_project_slug(task)
    files: list[str] = []
    ignored_top_level = {
        "main.py",
        "main_langgraph.py",
        "run_all_cases.py",
        "run_capability_suite.py",
        "run_company_agents_demo.py",
        "run_global_supervisor_demo.py",
        "run_software_factory_demo.py",
    }
    command_prefixes = ("python ", "python3 ", "py ")
    for line in task.splitlines():
        stripped = line.strip()
        is_command_line = stripped.startswith(command_prefixes)
        for match in re.finditer(r"(?<![\w.-])([\w./\\-]+\.py)(?![\w.-])", line):
            item = _normalize_path(match.group(1))
            has_folder = "/" in item
            if project != "generated_project":
                if has_folder and not item.startswith(f"{project}/"):
                    continue
                if not has_folder and (is_command_line or item in ignored_top_level):
                    continue
                if not has_folder:
                    item = f"{project}/{item}"
            if item not in files:
                files.append(item)
    return files


def infer_project_slug(task: str) -> str:
    fenced = re.search(r"`([\w.-]+)`", task)
    if fenced:
        return fenced.group(1).strip("`")
    folder = re.search(r"(?im)^\s*([A-Za-z_][\w-]*)/\s*$", task)
    if folder:
        return folder.group(1)
    if "society_sim" in task:
        return "society_sim"
    return "generated_project"


def infer_domain_profile(task: str) -> dict[str, Any]:
    folded = task.lower()
    project = infer_project_slug(task)
    files = extract_requested_files(task)

    if any(token in folded for token in ("simulation", "world", "person", "relationship", "job", "house")):
        return {
            "project": project,
            "domain": "life-simulation engine",
            "actors": ["player/operator", "simulated person", "world clock"],
            "objects": [
                "Person",
                "House",
                "Job",
                "WorldEvent",
                "WorldState",
                "Simulation",
                "Persistence",
            ],
            "workflows": [
                "create default world",
                "advance one tick",
                "choose automatic person action",
                "apply action effects",
                "summarize world state",
                "save and load world state",
                "run terminal demo",
            ],
            "hotspots": [
                "need decay rates",
                "action priority rules",
                "job schedule and salary rules",
                "relationship changes",
                "world persistence schema",
                "summary/reporting fields",
                "test and demo execution markers",
            ],
            "nfrs": [
                "stdlib-only Python",
                "deterministic terminal execution",
                "no graphics dependency",
                "plain assert tests",
                "save/load compatibility",
            ],
            "requested_files": files,
        }

    return {
        "project": project,
        "domain": "software product",
        "actors": ["user", "operator", "system"],
        "objects": ["UserGoal", "Workflow", "Policy", "DataStore", "Interface"],
        "workflows": ["capture goal", "execute workflow", "validate output", "report result"],
        "hotspots": ["business rules", "integration boundaries", "data schema", "validation strategy"],
        "nfrs": ["maintainability", "testability", "observability", "small dependency surface"],
        "requested_files": files,
    }


def _artifact(context: dict[str, Any], key: str) -> ArtifactRef | None:
    value = context.setdefault("artifacts", {}).get(key)
    return value if isinstance(value, ArtifactRef) else None


def _required_missing(context: dict[str, Any], keys: tuple[str, ...]) -> list[str]:
    return [key for key in keys if _artifact(context, key) is None]


def _artifact_links(context: dict[str, Any], keys: tuple[str, ...]) -> str:
    rows = []
    for key in keys:
        ref = _artifact(context, key)
        if ref:
            rows.append(f"- {key}: `{ref.path}`")
    return "\n".join(rows) if rows else "- No upstream artifacts yet."


def _task_excerpt(task: str) -> str:
    return brief_text(task, limit=1400)


def _count_terms(text: str, terms: tuple[str, ...]) -> int:
    return sum(1 for term in terms if term in text)


def infer_workload_mode(task: str) -> dict[str, Any]:
    folded = task.lower()
    business_terms = (
        "business",
        "brd",
        "prd",
        "epic",
        "story",
        "acceptance",
        "domain",
        "logic",
        "workflow",
        "policy",
        "stakeholder",
        "requirement",
    )
    coding_terms = (
        ".py",
        "code",
        "bug",
        "fix",
        "test",
        "function",
        "class",
        "module",
        "cli",
    )
    docs_terms = ("docs", "readme", "adr", "architecture", "api reference")
    business_score = _count_terms(folded, business_terms)
    coding_score = _count_terms(folded, coding_terms)
    docs_score = _count_terms(folded, docs_terms)

    reasons: list[str] = []
    if len(task) > 1800:
        reasons.append("prompt is long enough that inline JSON analysis is fragile")
    if business_score >= 2:
        reasons.append("business/product/domain terms are present")
    if "json" in folded and ("long" in folded or "parse" in folded or "too long" in folded):
        reasons.append("prompt explicitly mentions JSON parsing or length constraints")

    mode = "business_to_logic" if reasons else "coding_execution"
    if docs_score >= 2 and mode == "coding_execution":
        mode = "docs_evidence"
        reasons.append("documentation evidence terms are present")

    return {
        "mode": mode,
        "scores": {
            "business": business_score,
            "coding": coding_score,
            "documentation": docs_score,
        },
        "reasons": reasons or ["prompt is narrow enough for the normal coding contract"],
        "control_channel": "compact_json_envelope",
        "analysis_channel": "artifact_files",
        "max_inline_chars": 480,
        "json_policy": [
            "JSON carries routing, decisions, status, and artifact references only.",
            "Long BRD/PRD/domain/logic analysis must be written to markdown artifacts.",
            "Long structured inventories must be written to JSON artifacts and passed by path/hash.",
            "Coding tool calls can stay strict JSON because each call is a small action.",
        ],
        "artifact_policy": [
            "Business reasoning lives in versioned artifacts.",
            "Downstream agents must read artifact references instead of relying on pasted context.",
            "Every long artifact has a compact summary and sha256 in the stage envelope.",
        ],
    }


def infer_business_logic_contract(task: str) -> dict[str, Any]:
    profile = infer_domain_profile(task)
    if "life-simulation" in profile["domain"]:
        return {
            "invariants": [
                "Every need value stays in the inclusive range 0.0..100.0 after every tick and action.",
                "World time advances deterministically: 24 hours roll into the next day.",
                "A person can have at most one active home_id and one active job_id.",
                "Relationship updates from socialize are symmetric for actor and target.",
                "Save/load preserves population, houses, jobs, clock, and recent event data.",
            ],
            "decision_rows": [
                ("hunger < 35", "eat", "restore hunger and spend a small amount of money"),
                ("energy < 30", "sleep", "restore energy and slightly reduce social"),
                ("hygiene < 30", "clean", "restore hygiene"),
                ("current hour is inside assigned job schedule", "work", "earn salary and improve job skill"),
                ("social < 40", "socialize", "increase social and relationship score"),
                ("fun < 40", "play", "increase fun and reduce energy"),
                ("no urgent need", "idle", "make a small neutral recovery"),
            ],
            "state_transitions": [
                "Simulation.step increments tick, updates hour/day, then processes each person.",
                "Each person runs decay_needs -> choose_action -> apply_action -> calculate_mood.",
                "World events are appended for meaningful actions and daily rollovers.",
                "Simulation.run repeats step for a requested number of ticks and returns the final state.",
            ],
            "testable_examples": [
                "A hungry person chooses eat before work or play.",
                "A rested worker inside work hours earns money after one work action.",
                "Two people who socialize both receive increased relationship scores.",
                "A world saved to JSON and loaded back has the same population count.",
            ],
            "failure_modes": [
                "Need values drift outside 0..100.",
                "Socialize changes only one side of a relationship.",
                "Persistence serializes dataclasses but cannot reconstruct them.",
                "CLI demo claims success without exercising save/load.",
            ],
        }

    return {
        "invariants": [
            "Domain state changes only through explicit business rules.",
            "User-visible workflows have measurable success and failure outcomes.",
            "Validation evidence must exist before final completion is claimed.",
            "External side effects are isolated behind named boundaries.",
        ],
        "decision_rows": [
            ("user submits a goal", "capture_goal", "preserve intent, constraints, and acceptance signals"),
            ("workflow has ambiguous policy", "resolve_policy", "make rules explicit before technical design"),
            ("output affects files or external systems", "record_side_effect", "make side effects auditable"),
            ("validation evidence is missing", "block_completion", "route back to implementation or tests"),
        ],
        "state_transitions": [
            "Idea -> business requirement -> product behavior -> acceptance criterion.",
            "Acceptance criterion -> domain rule -> technical boundary -> implementation task.",
            "Implementation result -> validation evidence -> docs evidence -> final report.",
        ],
        "testable_examples": [
            "A workflow without acceptance criteria cannot enter technical design.",
            "A pattern without hotspot evidence is rejected.",
            "A final report without test evidence is incomplete.",
        ],
        "failure_modes": [
            "Business rules stay as prose and never become executable checks.",
            "Technical pattern is chosen before the volatile domain areas are known.",
            "Long analysis is pasted into a JSON route and fails parsing.",
        ],
    }


def _artifact_ref_dicts(context: dict[str, Any], keys: tuple[str, ...]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for key in keys:
        ref = _artifact(context, key)
        if ref:
            data = ref.to_dict()
            data["artifact_key"] = key
            refs.append(data)
    return refs


@dataclass
class FactoryDepartmentAgent:
    name: str
    department: str
    artifact_key: str
    filename: str
    kind: str
    title: str
    next_agent: str
    required_inputs: tuple[str, ...] = ()

    def run(self, task: str, context: dict[str, Any]) -> StageResult:
        missing = _required_missing(context, self.required_inputs)
        if missing:
            return stage_blocked(
                agent=self.name,
                department=self.department,
                missing_inputs=missing,
                route_next_agent=self.required_inputs[0] if self.required_inputs else "human",
                reason=f"{self.name} requires upstream artifacts before it can proceed.",
            )

        content = self.build_content(task, context)
        ref = write_text_artifact(
            context["artifact_dir"],
            self.filename,
            content,
            kind=self.kind,
            producer=self.name,
            title=self.title,
            summary=self.summary(task, context),
        )
        context.setdefault("artifacts", {})[self.artifact_key] = ref
        return StageResult(
            agent=self.name,
            department=self.department,
            decision=self.decision(task, context),
            route_next_agent=self.next_agent,
            artifact_refs=(ref,),
            notes=self.notes(task, context),
            metadata={
                "route_reason": f"{self.title} is available as an artifact reference.",
                "artifact_key": self.artifact_key,
            },
        )

    def build_content(self, task: str, context: dict[str, Any]) -> str:
        raise NotImplementedError

    def summary(self, task: str, context: dict[str, Any]) -> str:
        return self.title

    def decision(self, task: str, context: dict[str, Any]) -> str:
        return "artifact_created"

    def notes(self, task: str, context: dict[str, Any]) -> tuple[str, ...]:
        return ()


class IntakeProtocolAgent(FactoryDepartmentAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Intake Protocol Agent",
            department="Factory Operations Department",
            artifact_key="protocol_strategy",
            filename="00_protocol_strategy.json",
            kind="protocol_strategy",
            title="Protocol Strategy",
            next_agent="Product Vision Agent",
        )

    def run(self, task: str, context: dict[str, Any]) -> StageResult:
        strategy = infer_workload_mode(task)
        data = {
            "gate": "intake_protocol",
            "status": "pass",
            "task_mode": strategy["mode"],
            "control_channel": strategy["control_channel"],
            "analysis_channel": strategy["analysis_channel"],
            "max_inline_chars": strategy["max_inline_chars"],
            "scores": strategy["scores"],
            "reasons": strategy["reasons"],
            "json_policy": strategy["json_policy"],
            "artifact_policy": strategy["artifact_policy"],
            "handoff_rule": (
                "Use compact JSON for control and artifact refs; use artifact files "
                "for long business, product, domain, and logic content."
            ),
        }
        ref = write_json_artifact(
            context["artifact_dir"],
            self.filename,
            data,
            kind=self.kind,
            producer=self.name,
            title=self.title,
            summary=f"Selected {strategy['mode']} mode with artifact-first analysis.",
        )
        context.setdefault("artifacts", {})[self.artifact_key] = ref
        context["protocol_strategy"] = data
        return StageResult(
            agent=self.name,
            department=self.department,
            decision=f"protocol_selected:{strategy['mode']}",
            route_next_agent=self.next_agent,
            artifact_refs=(ref,),
            notes=("Long analysis will be passed by artifact reference, not inline JSON.",),
            metadata={
                "route_reason": "Protocol strategy selected before product analysis.",
                "task_mode": strategy["mode"],
                "max_inline_chars": strategy["max_inline_chars"],
            },
        )

    def build_content(self, task: str, context: dict[str, Any]) -> str:
        raise NotImplementedError


class ProductVisionAgent(FactoryDepartmentAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Product Vision Agent",
            department="Product Department",
            artifact_key="vision",
            filename="00_vision.md",
            kind="product_vision",
            title="Product Vision",
            next_agent="BRD Agent",
            required_inputs=("protocol_strategy",),
        )

    def build_content(self, task: str, context: dict[str, Any]) -> str:
        profile = infer_domain_profile(task)
        protocol = context.get("protocol_strategy", infer_workload_mode(task))
        task_mode = protocol.get("mode") or protocol.get("task_mode", "unknown")
        return f"""# Product Vision

## Inputs
{_artifact_links(context, ("protocol_strategy",))}

## Mission
Build `{profile["project"]}` as a useful, testable software product, not just a
code exercise.

## User Intent
{_task_excerpt(task)}

## Product Outcome
- Deliver a working {profile["domain"]}.
- Preserve the explicit constraints from the user prompt.
- Produce enough evidence for downstream coding, testing, review, and docs.

## Operating Mode
- Task mode: `{task_mode}`.
- Control channel: `{protocol.get("control_channel", "compact_json_envelope")}`.
- Analysis channel: `{protocol.get("analysis_channel", "artifact_files")}`.
- Long reasoning is stored as artifacts; JSON stays small and parseable.

## Non-Goals
- Do not choose implementation patterns in this document.
- Do not write code from the raw idea.
- Do not claim delivery before validation evidence exists.

## Success Signal
The factory can trace every code-facing requirement back to Vision, BRD, PRD,
Story, Acceptance Criteria, Domain Analysis, and Change Hotspots.
"""


class BRDAgent(FactoryDepartmentAgent):
    def __init__(self) -> None:
        super().__init__(
            name="BRD Agent",
            department="Business Analysis Department",
            artifact_key="brd",
            filename="01_brd.md",
            kind="business_requirements",
            title="Business Requirements Document",
            next_agent="PRD Agent",
            required_inputs=("vision",),
        )

    def build_content(self, task: str, context: dict[str, Any]) -> str:
        profile = infer_domain_profile(task)
        return f"""# Business Requirements Document

## Inputs
{_artifact_links(context, ("vision",))}

## Business Goals
- The product must satisfy the user-visible workflow described in the prompt.
- The product must be runnable locally with simple commands.
- The product must include validation evidence before it is considered done.

## Stakeholders
- Requesting user: wants a working local coding-agent outcome.
- Future maintainer: needs understandable modules, tests, and docs.
- QA/review roles: need measurable acceptance criteria.

## In-Scope Capabilities
{chr(10).join(f"- {workflow}" for workflow in profile["workflows"])}

## Constraints
{chr(10).join(f"- {nfr}" for nfr in profile["nfrs"])}

## Business Risks
- Ambiguous idea-to-code jumps can create the wrong product.
- Early pattern selection can overfit design before real variation is known.
- Missing validation creates false completion.

## Explicit Rule
This BRD does not select technical patterns. It only defines business need,
scope, constraints, and measurable outcomes.
"""


class PRDAgent(FactoryDepartmentAgent):
    def __init__(self) -> None:
        super().__init__(
            name="PRD Agent",
            department="Product Department",
            artifact_key="prd",
            filename="02_prd.md",
            kind="product_requirements",
            title="Product Requirements Document",
            next_agent="Epic Story Agent",
            required_inputs=("vision", "brd"),
        )

    def build_content(self, task: str, context: dict[str, Any]) -> str:
        profile = infer_domain_profile(task)
        files = profile["requested_files"] or ["implementation files to be inferred by Architect"]
        return f"""# Product Requirements Document

## Inputs
{_artifact_links(context, ("vision", "brd"))}

## Functional Requirements
{chr(10).join(f"- Support workflow: {workflow}." for workflow in profile["workflows"])}

## Required Interfaces
- CLI or script entrypoint for local execution.
- Automated validation command.
- Final report with files changed, test evidence, limits, and next steps.

## Requested Files or Modules
{chr(10).join(f"- `{file}`" for file in files)}

## Product-Level Quality Requirements
{chr(10).join(f"- {nfr}." for nfr in profile["nfrs"])}

## Out of Scope
- Unrequested external packages.
- Unrequested UI or graphics.
- Repository-wide refactors outside the target scope.

## Product Rule
The PRD is still not allowed to choose design patterns. It prepares stories and
acceptance criteria for later analysis.
"""


class EpicStoryAgent(FactoryDepartmentAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Epic Story Agent",
            department="Product Department",
            artifact_key="stories",
            filename="03_epics_stories.md",
            kind="epics_stories",
            title="Epics and Stories",
            next_agent="Acceptance Criteria Agent",
            required_inputs=("prd",),
        )

    def build_content(self, task: str, context: dict[str, Any]) -> str:
        profile = infer_domain_profile(task)
        stories = []
        for index, workflow in enumerate(profile["workflows"], start=1):
            stories.append(
                f"### Story S{index:02d}: {workflow.title()}\n"
                f"As a user, I want the system to {workflow}, so that the product can "
                "deliver a visible and testable outcome."
            )
        return f"""# Epics and Stories

## Inputs
{_artifact_links(context, ("prd",))}

## Epic E01: Deliver the Core Product Workflow
{chr(10).join(stories)}

## Epic E02: Make the Product Verifiable
### Story S90: Automated Validation
As a maintainer, I want deterministic tests or checks, so that completion is
based on evidence instead of prose.

### Story S91: User-Facing Completion Report
As the requesting user, I want a concise final report, so that I know what was
built, how it was validated, and what limits remain.
"""


class AcceptanceCriteriaAgent(FactoryDepartmentAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Acceptance Criteria Agent",
            department="Product Department",
            artifact_key="acceptance_criteria",
            filename="04_acceptance_criteria.md",
            kind="acceptance_criteria",
            title="Acceptance Criteria",
            next_agent="Product Spec Validator Agent",
            required_inputs=("stories",),
        )

    def build_content(self, task: str, context: dict[str, Any]) -> str:
        profile = infer_domain_profile(task)
        items = []
        for index, workflow in enumerate(profile["workflows"], start=1):
            items.append(
                f"- AC{index:02d}: `{workflow}` is implemented with a local, repeatable check."
            )
        if profile["requested_files"]:
            items.append("- AC80: All explicitly requested files exist in the target project folder.")
        items.extend(
            [
                "- AC90: Automated validation runs and reports a clear success marker or passing result.",
                "- AC91: The final answer names validation evidence and current limits.",
                "- AC92: No out-of-scope repository files are modified without an explicit reason.",
            ]
        )
        return f"""# Acceptance Criteria

## Inputs
{_artifact_links(context, ("stories",))}

## Criteria
{chr(10).join(items)}

## Gate Rule
No technical design or pattern decision may start until these criteria exist.
"""


class ProductSpecValidatorAgent(FactoryDepartmentAgent):
    REQUIRED = ("protocol_strategy", "vision", "brd", "prd", "stories", "acceptance_criteria")

    def __init__(self) -> None:
        super().__init__(
            name="Product Spec Validator Agent",
            department="Product Quality Department",
            artifact_key="product_validation",
            filename="05_product_spec_validation.json",
            kind="product_spec_validation",
            title="Product Spec Validation",
            next_agent="Product Spec Critic Agent",
            required_inputs=self.REQUIRED,
        )

    def run(self, task: str, context: dict[str, Any]) -> StageResult:
        missing = _required_missing(context, self.REQUIRED)
        data = {
            "gate": "product_spec",
            "status": "pass" if not missing else "fail",
            "required_artifacts": list(self.REQUIRED),
            "missing": missing,
            "rules": [
                "No protocol strategy -> no long analysis handoff.",
                "No Vision -> no BRD.",
                "No BRD -> no PRD.",
                "No Story + AC -> no technical design.",
            ],
        }
        ref = write_json_artifact(
            context["artifact_dir"],
            self.filename,
            data,
            kind=self.kind,
            producer=self.name,
            title=self.title,
            summary=f"Product spec gate {data['status']}.",
        )
        context.setdefault("artifacts", {})[self.artifact_key] = ref
        return StageResult(
            agent=self.name,
            department=self.department,
            ok=not missing,
            decision="product_spec_valid" if not missing else "blocked_missing_product_spec",
            route_next_agent=self.next_agent if not missing else "Product Vision Agent",
            artifact_refs=(ref,),
            missing_inputs=tuple(missing),
            notes=("Product spec chain is complete." if not missing else "Product spec chain is incomplete.",),
            metadata={"route_reason": "Product spec validation completed.", "gate_status": data["status"]},
        )

    def build_content(self, task: str, context: dict[str, Any]) -> str:
        raise NotImplementedError


class ProductSpecCriticAgent(FactoryDepartmentAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Product Spec Critic Agent",
            department="Product Review Department",
            artifact_key="product_critique",
            filename="06_product_spec_critique.md",
            kind="product_spec_critique",
            title="Product Spec Critique",
            next_agent="Domain Analyst Agent",
            required_inputs=("product_validation",),
        )

    def build_content(self, task: str, context: dict[str, Any]) -> str:
        risky_terms = [term for term in ("singleton", "observer", "factory", "strategy", "ecs") if term in task.lower()]
        warning = (
            "- The raw prompt mentions pattern-like terms; keep them as hypotheses only."
            if risky_terms
            else "- No early pattern commitment found in the raw prompt."
        )
        return f"""# Product Spec Critique

## Inputs
{_artifact_links(context, ("protocol_strategy", "vision", "brd", "prd", "stories", "acceptance_criteria", "product_validation"))}

## Critique
{warning}
- Product requirements are traceable enough to enter domain analysis.
- Acceptance criteria include validation and final-report obligations.
- Technical choices remain deferred until change hotspots are known.

## Required Next Step
Domain Analyst must identify domain objects, use-case flows, side effects,
integration boundaries, non-functional requirements, and change hotspots.
"""


class DomainAnalystAgent(FactoryDepartmentAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Domain Analyst Agent",
            department="Domain Analysis Department",
            artifact_key="domain_analysis",
            filename="07_domain_analysis.md",
            kind="domain_analysis",
            title="Domain Analysis and Change Hotspots",
            next_agent="Business Logic Model Agent",
            required_inputs=("product_critique", "acceptance_criteria"),
        )

    def build_content(self, task: str, context: dict[str, Any]) -> str:
        profile = infer_domain_profile(task)
        return f"""# Domain Analysis and Change Hotspots

## Inputs
{_artifact_links(context, ("prd", "stories", "acceptance_criteria", "product_critique"))}

## Domain
{profile["domain"]}

## Actors
{chr(10).join(f"- {actor}" for actor in profile["actors"])}

## Domain Objects
{chr(10).join(f"- {obj}" for obj in profile["objects"])}

## Use-Case Flows
{chr(10).join(f"- {flow}" for flow in profile["workflows"])}

## Change Hotspots
{chr(10).join(f"- {hotspot}" for hotspot in profile["hotspots"])}

## Side Effects
- File creation or update in the target workspace.
- Local command execution for validation.
- Optional save/load artifacts produced by the generated product.

## Non-Functional Requirements
{chr(10).join(f"- {nfr}" for nfr in profile["nfrs"])}

## Gate Rule
No pattern decision may be made without explicit hotspot evidence from this
document.
"""

    def metadata_hotspots(self, task: str) -> list[str]:
        return infer_domain_profile(task)["hotspots"]


class BusinessLogicModelAgent(FactoryDepartmentAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Business Logic Model Agent",
            department="Business Logic Department",
            artifact_key="business_logic_model",
            filename="08_business_logic_model.md",
            kind="business_logic_model",
            title="Business Logic Model",
            next_agent="Business Logic Validator Agent",
            required_inputs=("domain_analysis", "acceptance_criteria"),
        )

    def build_content(self, task: str, context: dict[str, Any]) -> str:
        profile = infer_domain_profile(task)
        contract = infer_business_logic_contract(task)
        decision_table = "\n".join(
            f"| {condition} | {action} | {outcome} |"
            for condition, action, outcome in contract["decision_rows"]
        )
        return f"""# Business Logic Model

## Inputs
{_artifact_links(context, ("domain_analysis", "acceptance_criteria"))}

## Purpose
Convert business/product/domain analysis into a logic contract that Code and
Test agents can implement without reinterpreting the business intent.

## Domain
{profile["domain"]}

## Invariants
{chr(10).join(f"- {item}" for item in contract["invariants"])}

## Decision Table
| Condition | Rule or Action | Expected Outcome |
| --- | --- | --- |
{decision_table}

## State Transitions
{chr(10).join(f"- {item}" for item in contract["state_transitions"])}

## Testable Examples
{chr(10).join(f"- {item}" for item in contract["testable_examples"])}

## Failure Modes to Guard
{chr(10).join(f"- {item}" for item in contract["failure_modes"])}

## Logic Handoff Rule
This artifact is the bridge from business analysis to executable logic. The
Code Agent may choose implementation syntax, but it must preserve these
invariants, decision rules, and testable examples unless it routes back to
business analysis with a concrete conflict.
"""

    def decision(self, task: str, context: dict[str, Any]) -> str:
        return "business_logic_contract_created"


class BusinessLogicValidatorAgent(FactoryDepartmentAgent):
    REQUIRED = ("domain_analysis", "business_logic_model", "acceptance_criteria")

    def __init__(self) -> None:
        super().__init__(
            name="Business Logic Validator Agent",
            department="Business Logic Quality Department",
            artifact_key="business_logic_validation",
            filename="08_business_logic_validation.json",
            kind="business_logic_validation",
            title="Business Logic Validation",
            next_agent="Technical Analyst Agent",
            required_inputs=self.REQUIRED,
        )

    def run(self, task: str, context: dict[str, Any]) -> StageResult:
        missing = _required_missing(context, self.REQUIRED)
        model_ref = _artifact(context, "business_logic_model")
        model_text = read_artifact_text(model_ref) if model_ref else ""
        checks = {
            "has_invariants": "## Invariants" in model_text,
            "has_decision_table": "## Decision Table" in model_text,
            "has_state_transitions": "## State Transitions" in model_text,
            "has_testable_examples": "## Testable Examples" in model_text,
            "has_failure_modes": "## Failure Modes to Guard" in model_text,
        }
        status = "pass" if not missing and all(checks.values()) else "fail"
        data = {
            "gate": "business_logic",
            "status": status,
            "required_artifacts": list(self.REQUIRED),
            "missing": missing,
            "checks": checks,
            "rule": "No business logic contract -> no technical analysis or pattern decision.",
        }
        ref = write_json_artifact(
            context["artifact_dir"],
            self.filename,
            data,
            kind=self.kind,
            producer=self.name,
            title=self.title,
            summary=f"Business logic validation {status}.",
        )
        context.setdefault("artifacts", {})[self.artifact_key] = ref
        return StageResult(
            agent=self.name,
            department=self.department,
            ok=status == "pass",
            decision="business_logic_valid" if status == "pass" else "business_logic_blocked",
            route_next_agent=self.next_agent if status == "pass" else "Business Logic Model Agent",
            artifact_refs=(ref,),
            missing_inputs=tuple(missing),
            notes=(
                "Business logic contract is ready for technical analysis."
                if status == "pass"
                else "Business logic contract is incomplete.",
            ),
            metadata={"route_reason": "Business logic validation completed.", "gate_status": status},
        )

    def build_content(self, task: str, context: dict[str, Any]) -> str:
        raise NotImplementedError


class TechnicalAnalystAgent(FactoryDepartmentAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Technical Analyst Agent",
            department="Technical Analysis Department",
            artifact_key="technical_analysis",
            filename="08_technical_analysis.md",
            kind="technical_analysis",
            title="Technical Analysis",
            next_agent="Pattern Decision Agent",
            required_inputs=("domain_analysis", "business_logic_validation"),
        )

    def build_content(self, task: str, context: dict[str, Any]) -> str:
        profile = infer_domain_profile(task)
        files = profile["requested_files"] or ["files to be chosen by engineering from the implementation spec"]
        return f"""# Technical Analysis

## Inputs
{_artifact_links(context, ("domain_analysis", "business_logic_model", "business_logic_validation"))}

## Module Boundaries
{chr(10).join(f"- `{file}`" for file in files)}

## Business Logic Boundary
- Implement the Business Logic Model as explicit rules, policies, or pure
  functions before wiring CLI, persistence, or reporting.
- Treat decision tables and invariants as test inputs, not as optional prose.
- If the logic contract conflicts with requested files or constraints, route
  back to Business Logic Model instead of inventing a new pattern.

## Data and State
- Keep business/domain state separate from CLI/demo/reporting code.
- Keep persistence isolated from simulation or workflow logic.
- Keep validation scripts deterministic and local.

## Integration Boundaries
- Local filesystem for source files and generated runtime artifacts.
- Local Python runtime for validation.
- No external packages unless the user explicitly allows them.

## Risk Analysis
- Long, business-heavy prompts can exceed JSON comfort limits.
- Coding agents may overstep into planning if artifact gates are missing.
- A passing test marker must be observed before finish.

## Rule
This document may describe module boundaries and risks, but it still does not
select a design pattern. Pattern choice needs hotspot-to-module evidence.
"""


class PatternDecisionAgent(FactoryDepartmentAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Pattern Decision Agent",
            department="Architecture Decision Department",
            artifact_key="pattern_decision",
            filename="09_pattern_decision.md",
            kind="pattern_decision",
            title="Pattern Decision",
            next_agent="Implementation Spec Agent",
            required_inputs=("domain_analysis", "business_logic_validation", "technical_analysis"),
        )

    def build_content(self, task: str, context: dict[str, Any]) -> str:
        profile = infer_domain_profile(task)
        hotspot_rows = "\n".join(f"- {item}" for item in profile["hotspots"])
        if "life-simulation" in profile["domain"]:
            decisions = [
                {
                    "pattern": "Domain Model with dataclasses",
                    "problem": "Multiple domain objects need explicit state and serialization.",
                    "without": "State would spread across loose dictionaries and tests would be brittle.",
                    "risk": "Low; dataclasses are stdlib and match the requested model objects.",
                    "module": "models.py",
                    "evidence": ["Domain Objects", "save/load compatibility"],
                },
                {
                    "pattern": "Pure rule functions",
                    "problem": "Need/action/mood rules are the primary change hotspot.",
                    "without": "Simulation step would become a large conditional block that is hard to test.",
                    "risk": "Low; functions are simpler than a class hierarchy or strategy framework.",
                    "module": "rules.py",
                    "evidence": [
                        "need decay rates",
                        "action priority rules",
                        "relationship changes",
                        "Business Logic Model decision table",
                    ],
                },
                {
                    "pattern": "Small persistence adapter",
                    "problem": "Save/load is a side effect that should not pollute domain logic.",
                    "without": "Serialization details would leak into simulation and tests.",
                    "risk": "Low; only one adapter module, no repository framework.",
                    "module": "persistence.py",
                    "evidence": ["world persistence schema", "save/load compatibility"],
                },
            ]
        else:
            decisions = [
                {
                    "pattern": "Layered core with explicit boundaries",
                    "problem": "Business rules, I/O, and validation need separate change surfaces.",
                    "without": "Future changes would mix policy, execution, and reporting.",
                    "risk": "Medium; keep layers as files/modules, not abstract frameworks.",
                    "module": "core modules",
                    "evidence": profile["hotspots"][:3],
                }
            ]
        lines = []
        for index, decision in enumerate(decisions, start=1):
            lines.append(
                f"### Decision P{index:02d}: {decision['pattern']}\n"
                f"- Problem solved: {decision['problem']}\n"
                f"- Why needed now: evidence exists in change hotspots.\n"
                f"- If not used: {decision['without']}\n"
                f"- Overengineering risk: {decision['risk']}\n"
                f"- Target module: `{decision['module']}`\n"
                f"- Trace: {', '.join(decision['evidence'])}"
            )
        return f"""# Pattern Decision

## Inputs
{_artifact_links(context, ("domain_analysis", "business_logic_model", "business_logic_validation", "technical_analysis"))}

## Change Hotspot Evidence
{hotspot_rows}

## Business Logic Evidence
Pattern choices must preserve the logic contract. If a pattern does not make
invariants, decision tables, state transitions, or validation examples easier
to implement and test, it is rejected.

## Decisions
{chr(10).join(lines)}

## Explicit Rejections
- Do not introduce a framework-sized pattern without repeated variation.
- Do not use Observer/Event Bus for a small terminal simulation until event
  consumers multiply.
- Do not use ECS unless entity/component variation becomes the main problem.

## Gate Rule
Code may start only after each selected pattern traces to a hotspot, story, or
acceptance criterion.
"""

    def decision(self, task: str, context: dict[str, Any]) -> str:
        return "pattern_decision_has_hotspot_evidence"


class ImplementationSpecAgent(FactoryDepartmentAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Implementation Spec Agent",
            department="Architecture Department",
            artifact_key="implementation_spec",
            filename="10_implementation_spec.md",
            kind="implementation_spec",
            title="Implementation Specification",
            next_agent="Code Handoff Packager Agent",
            required_inputs=("business_logic_model", "business_logic_validation", "pattern_decision"),
        )

    def build_content(self, task: str, context: dict[str, Any]) -> str:
        profile = infer_domain_profile(task)
        files = profile["requested_files"]
        if not files:
            files = [f"{profile['project']}/__init__.py", f"{profile['project']}/main.py", f"{profile['project']}/test_main.py"]
        return f"""# Implementation Specification

## Inputs
{_artifact_links(context, ("protocol_strategy", "vision", "brd", "prd", "stories", "acceptance_criteria", "domain_analysis", "business_logic_model", "business_logic_validation", "technical_analysis", "pattern_decision"))}

## Target Project
`{profile["project"]}`

## Files to Create or Modify
{chr(10).join(f"- `{file}`" for file in files)}

## Implementation Order
1. Create the target folder.
2. Create data/domain models first.
3. Create pure business rules or service logic.
4. Create orchestration/runtime logic.
5. Create persistence or I/O adapters.
6. Create CLI/demo entrypoints.
7. Create tests last, then run tests and demo.

## Business Logic Contract
- Implement the invariants and decision table from `business_logic_model`.
- Convert each testable example into an assert-based, unit, or integration
  check appropriate to the project.
- Do not reinterpret business rules inside CLI, persistence, or reporting code.

## Coding Agent Contract
- Stay inside the requested target folder unless this spec says otherwise.
- Use the smallest implementation that satisfies acceptance criteria.
- Do not choose new design patterns during coding without returning to Pattern Decision.
- Use file editor tools for source edits and terminal/python tools only for validation.
- Return docs metadata: implemented_files, entrypoints, test_commands, env_vars,
  public_interfaces, and docs_notes.
- Keep tool-call JSON small. If the implementation needs long reasoning,
  write or read artifacts and pass compact references instead.

## Expected Compact Code Result Shape
```json
{stable_json({
    "decision": "implemented_or_blocked",
    "implemented_files": ["path/to/file.py"],
    "test_commands": [{"command": "python path/to/test.py", "status": "pass|fail"}],
    "docs_metadata_ref": "artifact path when metadata is long",
})}
```

## Suggested Validation
- Run the project test command from the prompt if present.
- Run the demo or entrypoint if present.
- Finish only when validation passes or a concrete blocker is reported.

## Original User Prompt
```text
{_task_excerpt(task)}
```
"""

    def decision(self, task: str, context: dict[str, Any]) -> str:
        return "ready_for_code_agent"


class CodeHandoffPackagerAgent(FactoryDepartmentAgent):
    READ_ORDER = (
        "protocol_strategy",
        "vision",
        "brd",
        "prd",
        "stories",
        "acceptance_criteria",
        "domain_analysis",
        "business_logic_model",
        "business_logic_validation",
        "technical_analysis",
        "pattern_decision",
        "implementation_spec",
    )

    def __init__(self) -> None:
        super().__init__(
            name="Code Handoff Packager Agent",
            department="Engineering Operations Department",
            artifact_key="code_handoff_packet",
            filename="11_code_handoff_packet.json",
            kind="code_handoff_packet",
            title="Code Handoff Packet",
            next_agent="Docs Orchestrator Agent",
            required_inputs=("implementation_spec", "business_logic_model", "business_logic_validation"),
        )

    def run(self, task: str, context: dict[str, Any]) -> StageResult:
        missing = _required_missing(context, self.required_inputs)
        if missing:
            return stage_blocked(
                agent=self.name,
                department=self.department,
                missing_inputs=missing,
                route_next_agent="Implementation Spec Agent",
                reason="Code handoff requires implementation and business logic artifacts.",
            )

        strategy = context.get("protocol_strategy", infer_workload_mode(task))
        data = {
            "gate": "code_handoff",
            "status": "ready_for_code_agent",
            "handoff_mode": "artifact_reference_first",
            "task_mode": strategy.get("mode") or strategy.get("task_mode"),
            "max_inline_chars": strategy.get("max_inline_chars", 480),
            "read_order": list(self.READ_ORDER),
            "artifact_refs": _artifact_ref_dicts(context, self.READ_ORDER),
            "code_agent_must": [
                "Read implementation_spec before writing files.",
                "Preserve business_logic_model invariants and decision table.",
                "Use strict JSON only for small control/tool actions.",
                "Run validation commands and report observed stdout/stderr markers.",
                "Return docs metadata or a docs metadata artifact reference.",
            ],
            "code_agent_must_not": [
                "Paste long business analysis into JSON tool arguments.",
                "Choose new design patterns without routing back to Pattern Decision.",
                "Claim test success without observed validation output.",
            ],
            "completion_requires": [
                "implemented files match implementation_spec",
                "tests or checks exercise acceptance criteria and logic examples",
                "docs metadata is available for Docs Department",
            ],
        }
        ref = write_json_artifact(
            context["artifact_dir"],
            self.filename,
            data,
            kind=self.kind,
            producer=self.name,
            title=self.title,
            summary="Compact artifact-reference packet for the Code Agent.",
        )
        context.setdefault("artifacts", {})[self.artifact_key] = ref
        return StageResult(
            agent=self.name,
            department=self.department,
            decision="code_handoff_packet_ready",
            route_next_agent=self.next_agent,
            artifact_refs=(ref,),
            notes=("Code Agent handoff is compact JSON with artifact references.",),
            metadata={
                "route_reason": "Implementation spec has been packaged for the coding pipeline.",
                "handoff_mode": data["handoff_mode"],
                "artifact_ref_count": len(data["artifact_refs"]),
            },
        )

    def build_content(self, task: str, context: dict[str, Any]) -> str:
        raise NotImplementedError


class DocsOrchestratorAgent(FactoryDepartmentAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Docs Orchestrator Agent",
            department="Documentation Department",
            artifact_key="docs_plan",
            filename="11_docs_plan.md",
            kind="docs_plan",
            title="Documentation Plan",
            next_agent="Repo Scanner Agent",
            required_inputs=("implementation_spec", "code_handoff_packet"),
        )

    def build_content(self, task: str, context: dict[str, Any]) -> str:
        return f"""# Documentation Plan

## Inputs
{_artifact_links(context, ("implementation_spec", "code_handoff_packet"))}

## Documentation Jobs
- Repo Scanner: identify real files, entrypoints, tests, docs, and generated artifacts.
- API Extractor: list public classes/functions and command entrypoints.
- ADR Recorder: capture architectural decisions with evidence.
- Docs Writer: compile usage, architecture, testing, and limitations from evidence.
- Docs Verifier: reject docs that mention missing paths, commands, env vars, or APIs.
- Business Logic Verifier: ensure docs explain the logic contract only from
  accepted artifacts and observed code/test evidence.

## Docs Rule
Docs are compiled from repo evidence and stage artifacts. They are not marketing
copy and should not claim unverified behavior.
"""


class RepoScannerAgent(FactoryDepartmentAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Repo Scanner Agent",
            department="Documentation Department",
            artifact_key="repo_scan",
            filename="12_repo_scan.json",
            kind="repo_scan",
            title="Repository Scan",
            next_agent="API Extractor Agent",
            required_inputs=("docs_plan",),
        )

    def run(self, task: str, context: dict[str, Any]) -> StageResult:
        missing = _required_missing(context, self.required_inputs)
        if missing:
            return stage_blocked(
                agent=self.name,
                department=self.department,
                missing_inputs=missing,
                route_next_agent="Docs Orchestrator Agent",
                reason="Repo scan requires a documentation plan.",
            )
        data = self._scan_repo(Path(context.get("repo_root", ".")))
        ref = write_json_artifact(
            context["artifact_dir"],
            self.filename,
            data,
            kind=self.kind,
            producer=self.name,
            title=self.title,
            summary=f"Scanned {data['file_count']} files for documentation evidence.",
        )
        context.setdefault("artifacts", {})[self.artifact_key] = ref
        return StageResult(
            agent=self.name,
            department=self.department,
            decision="repo_scan_complete",
            route_next_agent=self.next_agent,
            artifact_refs=(ref,),
            notes=(f"Scanned {data['file_count']} files; excluded heavy runtime folders.",),
            metadata={"route_reason": "Repository evidence is available.", "file_count": data["file_count"]},
        )

    def _scan_repo(self, root: Path) -> dict[str, Any]:
        exclude_parts = {".git", "__pycache__", "OpenHands", "qdrant_storage", "agent_runs", "test_runs"}
        files: list[str] = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [name for name in dirnames if name not in exclude_parts]
            current = Path(dirpath)
            for filename in filenames:
                if len(files) >= 250:
                    break
                path = current / filename
                if path.suffix.lower() not in {".py", ".md", ".json", ".yaml", ".yml", ".txt"}:
                    continue
                rel = path.relative_to(root)
                files.append(str(rel).replace("\\", "/"))
            if len(files) >= 250:
                break
        file_set = set(files)
        python_files = [path for path in files if path.endswith(".py")]
        markdown_files = [path for path in files if path.endswith(".md")]
        entrypoints = [
            path
            for path in python_files
            if Path(path).name in {"main.py", "cli_demo.py"} or Path(path).name.startswith("run_")
        ][:40]
        test_files = [path for path in python_files if Path(path).name.startswith("test_") or "_test" in Path(path).stem]
        agent_modules = [path for path in python_files if path.startswith("agents/") and path.endswith("_agent.py")]
        config_files = [
            path
            for path in files
            if Path(path).name
            in {
                "requirements.txt",
                "pyproject.toml",
                "docker-compose.yml",
                "mkdocs.yml",
                ".env.example",
            }
        ]
        project_type = "python_project" if python_files else "unknown"
        if agent_modules:
            project_type = "multi_agent_python_system"
        if any(path.startswith("mcp_servers/") for path in python_files):
            project_type = "multi_agent_mcp_python_system"
        test_commands = [f"python {path}" for path in test_files[:20]]
        if "run_software_factory_smoke.py" in file_set:
            test_commands.append("python run_software_factory_smoke.py")
        risks = []
        if not test_files:
            risks.append("No test files found in scanned sample.")
        if not any(Path(path).name == "requirements.txt" for path in files):
            risks.append("No requirements.txt found in scanned sample.")
        if len(files) >= 250:
            risks.append("Repo scan was truncated; docs must avoid claiming full coverage.")
        return {
            "repo_root": str(root.resolve()),
            "project_type": project_type,
            "file_count": len(files),
            "sample_files": files[:250],
            "important_files": [path for path in files if path in config_files or path in entrypoints][:80],
            "entrypoints": entrypoints,
            "install_commands": ["python -m pip install -r requirements.txt"] if "requirements.txt" in file_set else [],
            "run_commands": [f"python {path}" for path in entrypoints[:20]],
            "test_commands": test_commands,
            "config_files": config_files,
            "docs_files": markdown_files[:60],
            "agent_modules": agent_modules[:60],
            "risks": risks,
            "truncated": len(files) >= 250,
        }

    def build_content(self, task: str, context: dict[str, Any]) -> str:
        raise NotImplementedError


class APIExtractorAgent(FactoryDepartmentAgent):
    def __init__(self) -> None:
        super().__init__(
            name="API Extractor Agent",
            department="Documentation Department",
            artifact_key="api_inventory",
            filename="13_api_inventory.json",
            kind="api_inventory",
            title="API Inventory",
            next_agent="Architecture Decision Recorder Agent",
            required_inputs=("repo_scan",),
        )

    def run(self, task: str, context: dict[str, Any]) -> StageResult:
        missing = _required_missing(context, self.required_inputs)
        if missing:
            return stage_blocked(
                agent=self.name,
                department=self.department,
                missing_inputs=missing,
                route_next_agent="Repo Scanner Agent",
                reason="API extraction requires a repo scan.",
            )
        data = self._extract(Path(context.get("repo_root", ".")))
        ref = write_json_artifact(
            context["artifact_dir"],
            self.filename,
            data,
            kind=self.kind,
            producer=self.name,
            title=self.title,
            summary=f"Extracted API inventory from {data['python_file_count']} Python files.",
        )
        context.setdefault("artifacts", {})[self.artifact_key] = ref
        return StageResult(
            agent=self.name,
            department=self.department,
            decision="api_inventory_complete",
            route_next_agent=self.next_agent,
            artifact_refs=(ref,),
            notes=(f"Extracted classes/functions from {data['python_file_count']} Python files.",),
            metadata={
                "route_reason": "API inventory is available.",
                "python_file_count": data["python_file_count"],
            },
        )

    def _annotation(self, node: ast.AST | None) -> str | None:
        if node is None:
            return None
        try:
            return ast.unparse(node)
        except Exception:
            return None

    def _function_detail(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> dict[str, Any]:
        args = []
        for arg in node.args.args:
            args.append(
                {
                    "name": arg.arg,
                    "annotation": self._annotation(arg.annotation),
                }
            )
        side_effect_hints = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                name = ""
                if isinstance(child.func, ast.Attribute):
                    name = child.func.attr
                elif isinstance(child.func, ast.Name):
                    name = child.func.id
                if name in {"open", "write_text", "write_bytes", "mkdir", "remove", "unlink", "call_tool"}:
                    side_effect_hints.append(name)
        return {
            "name": node.name,
            "async": isinstance(node, ast.AsyncFunctionDef),
            "args": args,
            "returns": self._annotation(node.returns),
            "doc": brief_text(ast.get_docstring(node), limit=220) if ast.get_docstring(node) else None,
            "side_effect_hints": sorted(set(side_effect_hints)),
        }

    def _extract(self, root: Path) -> dict[str, Any]:
        exclude_parts = {".git", "__pycache__", "OpenHands", "qdrant_storage", "agent_runs", "test_runs"}
        modules: list[dict[str, Any]] = []
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [name for name in dirnames if name not in exclude_parts]
            current = Path(dirpath)
            for filename in filenames:
                if len(modules) >= 160:
                    break
                if not filename.endswith(".py"):
                    continue
                path = current / filename
                rel = path.relative_to(root)
                try:
                    tree = ast.parse(path.read_text(encoding="utf-8"))
                except Exception:
                    continue
                classes = [node.name for node in tree.body if isinstance(node, ast.ClassDef)]
                functions = [node.name for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
                function_details = [
                    self._function_detail(node)
                    for node in tree.body
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                ]
                class_details = []
                for node in tree.body:
                    if not isinstance(node, ast.ClassDef):
                        continue
                    methods = [
                        self._function_detail(item)
                        for item in node.body
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
                    ]
                    class_details.append(
                        {
                            "name": node.name,
                            "doc": brief_text(ast.get_docstring(node), limit=220) if ast.get_docstring(node) else None,
                            "methods": methods[:30],
                        }
                    )
                if classes or functions:
                    modules.append(
                        {
                            "path": str(rel).replace("\\", "/"),
                            "classes": classes,
                            "functions": functions,
                            "class_details": class_details,
                            "function_details": function_details,
                        }
                    )
            if len(modules) >= 160:
                break
        return {
            "python_file_count": len(modules),
            "modules": modules,
        }

    def build_content(self, task: str, context: dict[str, Any]) -> str:
        raise NotImplementedError


class ArchitectureDecisionRecorderAgent(FactoryDepartmentAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Architecture Decision Recorder Agent",
            department="Documentation Department",
            artifact_key="adr_candidates",
            filename="14_adr_candidates.md",
            kind="adr_candidates",
            title="ADR Candidates",
            next_agent="Docs Writer Agent",
            required_inputs=("pattern_decision", "api_inventory"),
        )

    def build_content(self, task: str, context: dict[str, Any]) -> str:
        pattern_ref = _artifact(context, "pattern_decision")
        pattern_excerpt = brief_text(read_artifact_text(pattern_ref), limit=2200) if pattern_ref else ""
        return f"""# ADR Candidates

## Inputs
{_artifact_links(context, ("pattern_decision", "api_inventory"))}

## Candidate ADR-0006: Artifact-First Software Factory
- Status: Proposed
- Context: Business and product analysis can be too long for strict tool-call JSON.
- Decision: Store long analysis in versioned artifacts and pass compact JSON
  references through the agent protocol.
- Consequences: Better parse reliability, easier audit, and clearer handoff to
  coding agents. Requires artifact cleanup/retention policy later.

## Candidate ADR-0007: Pattern Decisions Require Hotspot Evidence
- Status: Proposed
- Context: Product specs should not select design patterns directly.
- Decision: Pattern Decision Agent must map every pattern to hotspot/story/AC evidence.
- Consequences: Reduces overengineering and keeps architecture traceable.

## Candidate ADR-0008: Business Logic Contract Before Architecture
- Status: Proposed
- Context: BRD/PRD artifacts can remain too high-level for coding agents.
- Decision: Add a Business Logic Department that converts domain analysis into
  invariants, decision tables, state transitions, failure modes, and testable
  examples before technical design.
- Consequences: Code/Test agents receive executable intent instead of broad
  business prose. The extra gate adds one artifact but reduces rework.

## Candidate ADR-0009: Compact Code Handoff Packet
- Status: Proposed
- Context: Strict JSON is still valuable for routing and tool calls, but not
  for long business reasoning.
- Decision: Package the Code Agent handoff as compact JSON containing artifact
  refs, read order, and output contract.
- Consequences: Keeps parse reliability while preserving access to full
  business/product/domain context.

## Pattern Evidence Excerpt
```text
{pattern_excerpt}
```
"""


class DocsWriterAgent(FactoryDepartmentAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Docs Writer Agent",
            department="Documentation Department",
            artifact_key="docs_package",
            filename="15_docs_package.md",
            kind="docs_package",
            title="Docs Package Draft",
            next_agent="Docs Verifier Agent",
            required_inputs=("docs_plan", "repo_scan", "api_inventory", "adr_candidates"),
        )

    def build_content(self, task: str, context: dict[str, Any]) -> str:
        return f"""# Docs Package Draft

## Evidence
{_artifact_links(context, ("protocol_strategy", "vision", "brd", "prd", "stories", "acceptance_criteria", "domain_analysis", "business_logic_model", "business_logic_validation", "implementation_spec", "code_handoff_packet", "repo_scan", "api_inventory", "adr_candidates"))}

## Start Here
Run Spec Factory first when the task has business/product ambiguity:

```powershell
python run_software_factory_demo.py --task-file prompts/the_sims_prompt.md
```

Then feed the implementation spec artifact to the real coding pipeline:

```powershell
python run_company_agents_demo.py --real --task-file <factory-run>/10_implementation_spec.md --real-max-steps 260
```

## Architecture Summary
- Product Department creates Vision, BRD, PRD, Stories, and AC.
- Product Quality gates completeness before technical design.
- Domain and Technical Analysis identify boundaries and change hotspots.
- Business Logic Department turns domain analysis into invariants, decision
  tables, state transitions, failure modes, and testable examples.
- Pattern Decision maps design choices to evidence.
- Engineering receives an implementation spec plus a compact code handoff
  packet, not a raw brainstorm.
- Documentation Department compiles docs from repo evidence and artifacts.

## Verification Rule
Docs must mention only paths, commands, APIs, and env vars supported by evidence.
"""


class DocsVerifierAgent(FactoryDepartmentAgent):
    REQUIRED = (
        "protocol_strategy",
        "business_logic_validation",
        "docs_plan",
        "repo_scan",
        "api_inventory",
        "adr_candidates",
        "docs_package",
        "implementation_spec",
        "code_handoff_packet",
    )

    def __init__(self) -> None:
        super().__init__(
            name="Docs Verifier Agent",
            department="Documentation Quality Department",
            artifact_key="docs_verification",
            filename="16_docs_verification.json",
            kind="docs_verification",
            title="Docs Verification",
            next_agent="Final Agent",
            required_inputs=self.REQUIRED,
        )

    def run(self, task: str, context: dict[str, Any]) -> StageResult:
        missing = _required_missing(context, self.REQUIRED)
        data = {
            "gate": "docs_verification",
            "status": "pass" if not missing else "fail",
            "missing": missing,
            "checks": {
                "has_protocol_strategy": _artifact(context, "protocol_strategy") is not None,
                "has_business_logic_validation": _artifact(context, "business_logic_validation") is not None,
                "has_docs_plan": _artifact(context, "docs_plan") is not None,
                "has_repo_scan": _artifact(context, "repo_scan") is not None,
                "has_api_inventory": _artifact(context, "api_inventory") is not None,
                "has_adr_candidates": _artifact(context, "adr_candidates") is not None,
                "has_docs_package": _artifact(context, "docs_package") is not None,
                "has_implementation_spec": _artifact(context, "implementation_spec") is not None,
                "has_code_handoff_packet": _artifact(context, "code_handoff_packet") is not None,
            },
            "overclaim_guard": "Docs package is artifact-based and must be reverified after code changes.",
        }
        ref = write_json_artifact(
            context["artifact_dir"],
            self.filename,
            data,
            kind=self.kind,
            producer=self.name,
            title=self.title,
            summary=f"Docs verification {data['status']}.",
        )
        context.setdefault("artifacts", {})[self.artifact_key] = ref
        return StageResult(
            agent=self.name,
            department=self.department,
            ok=not missing,
            decision="docs_verified" if not missing else "docs_blocked",
            route_next_agent=self.next_agent if not missing else "Docs Orchestrator Agent",
            artifact_refs=(ref,),
            missing_inputs=tuple(missing),
            notes=("Docs evidence gate passed." if not missing else "Docs evidence gate failed.",),
            metadata={"route_reason": "Docs verification completed.", "gate_status": data["status"]},
        )

    def build_content(self, task: str, context: dict[str, Any]) -> str:
        raise NotImplementedError


class FactoryFinalAgent(FactoryDepartmentAgent):
    def __init__(self) -> None:
        super().__init__(
            name="Final Agent",
            department="Communication Department",
            artifact_key="factory_final",
            filename="17_factory_final.md",
            kind="factory_final",
            title="Factory Final Summary",
            next_agent="done",
            required_inputs=("docs_verification", "implementation_spec", "code_handoff_packet"),
        )

    def build_content(self, task: str, context: dict[str, Any]) -> str:
        implementation = _artifact(context, "implementation_spec")
        handoff = _artifact(context, "code_handoff_packet")
        return f"""# Factory Final Summary

## Status
The software-factory specification pipeline is complete and ready for the real
Code/Test/Review/Ledger execution chain.

## Main Handoff
- Implementation spec: `{implementation.path if implementation else ""}`
- Code handoff packet: `{handoff.path if handoff else ""}`

## Important Rule
This run does not claim that product code has been implemented. It claims that
the gated business-to-technical specification is ready to hand off.

## Next Command
```powershell
python run_company_agents_demo.py --real --task-file {implementation.path if implementation else "<implementation_spec>"} --real-max-steps 260
```
"""

    def decision(self, task: str, context: dict[str, Any]) -> str:
        return "ready_for_real_code_test_review"


FACTORY_AGENTS: tuple[FactoryDepartmentAgent, ...] = (
    IntakeProtocolAgent(),
    ProductVisionAgent(),
    BRDAgent(),
    PRDAgent(),
    EpicStoryAgent(),
    AcceptanceCriteriaAgent(),
    ProductSpecValidatorAgent(),
    ProductSpecCriticAgent(),
    DomainAnalystAgent(),
    BusinessLogicModelAgent(),
    BusinessLogicValidatorAgent(),
    TechnicalAnalystAgent(),
    PatternDecisionAgent(),
    ImplementationSpecAgent(),
    CodeHandoffPackagerAgent(),
    DocsOrchestratorAgent(),
    RepoScannerAgent(),
    APIExtractorAgent(),
    ArchitectureDecisionRecorderAgent(),
    DocsWriterAgent(),
    DocsVerifierAgent(),
    FactoryFinalAgent(),
)


def factory_agent_catalog() -> list[dict[str, Any]]:
    return [
        {
            "name": agent.name,
            "department": agent.department,
            "artifact_key": agent.artifact_key,
            "artifact_kind": agent.kind,
            "filename": agent.filename,
            "required_inputs": list(agent.required_inputs),
            "next_agent": agent.next_agent,
        }
        for agent in FACTORY_AGENTS
    ]


def artifacts_to_manifest(context: dict[str, Any]) -> dict[str, Any]:
    artifacts = context.get("artifacts", {})
    return {
        key: value.to_dict()
        for key, value in sorted(artifacts.items())
        if isinstance(value, ArtifactRef)
    }


def compact_stage_results(results: list[StageResult]) -> list[dict[str, Any]]:
    return [result.to_dict() for result in results]


def final_factory_payload(context: dict[str, Any], results: list[StageResult]) -> dict[str, Any]:
    implementation_ref = _artifact(context, "implementation_spec")
    handoff_ref = _artifact(context, "code_handoff_packet")
    return {
        "status": "ready_for_real_code_test_review",
        "run_id": context.get("run_id"),
        "artifact_dir": str(context.get("artifact_dir")),
        "implementation_spec": implementation_ref.to_dict() if implementation_ref else None,
        "code_handoff_packet": handoff_ref.to_dict() if handoff_ref else None,
        "stage_count": len(results),
        "agent_count": len(FACTORY_AGENTS),
        "agents": factory_agent_catalog(),
        "artifacts": artifacts_to_manifest(context),
    }
