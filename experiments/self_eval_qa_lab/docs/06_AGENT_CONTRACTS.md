# Agent Contracts

## Run Planner

- Input: user question.
- Output: run plan JSON-like object.
- Must explain which major phases will run.
- Must hand off to Question Classifier.

## Question Classifier

- Input: user question and available lenses.
- Output: strict JSON.
- Must classify task type, complexity, lens need, suggested lenses.
- Must not answer the user.

## Workflow Router

- Input: question and classification.
- Output: workflow decision.
- Must pick one of `direct`, `assisted`, `deep`, `repo_debug`.
- Must name a routing reason.

## Simple Answer

- Input: user question.
- Output: concise baseline answer.
- Must not call tools or generate code unless explicitly requested.

## Critic

- Input: question and draft.
- Output: public critique only.
- Must name concrete missing risks, assumptions, or next steps.
- Must not rewrite the full answer.

## Answer Synthesizer

- Input: question, draft, critique.
- Output: final assisted answer.
- Must improve the draft instead of repeating the critic.

## Lens Answer

- Input: question and selected lenses.
- Output: one synthesized deep answer.
- Must not paste separate lens sections unless that is genuinely clearer.

## Repo Debug Path

- Input: repo/debug question and draft.
- Output: no-code diagnostic answer.
- Must prefer local evidence and avoid external baseline by default.

## ChatGPT Baseline

- Input: original question.
- Output: independent answer.
- Must not mention this lab.
- Must be included in comparison when available.

## Blind Evaluator

- Input: anonymized answers.
- Output: strict JSON scores.
- Must not know answer source names.

## Error Analyzer

- Input: revealed evaluation.
- Output: strict JSON error report.
- Must identify where our answer won/lost.

## Flow Observer

- Input: workflow trace, evaluation, cost info.
- Output: strict JSON process verdict.
- Must evaluate process quality, not just answer quality.

## Lesson Extractor

- Input: flow observation and error report.
- Output: proposal-only lessons.
- Must prefer routing lessons before prompt/lens updates.

## Critical Auditor

- Input: trace health, workflow trace, agent events, ChatGPT comparison.
- Output: strict JSON audit.
- Must flag repeated outputs, invalid JSON, role confusion, wasted agents, missing agents, and handoff loops.

## Evolution Decider

- Input: critical audit, flow observation, lessons, ChatGPT comparison.
- Output: proposal-only evolution decision.
- Must never apply changes automatically.
