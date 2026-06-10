Test Code/Test Department v0.5 runner.

Required behavior:

1. Do not modify the main LangGraph orchestrator.
2. Run the dedicated deterministic smoke when asked manually:
   `python run_code_test_agents_smoke.py`
3. The expected marker is:
   `CODE_TEST_AGENTS_V05_SMOKE_OK`
4. Manual demo command:
   `python run_code_test_agents_demo.py --version v0.5 --agent orchestrator --max-cycles 2`

Final response should explain that v0.5 has:

- Code Agent lens results
- Code synthesis
- gated Code executor
- ledger/issue integration
- Code route decision
- Test Agent lens results
- Test synthesis
- allowlisted Test executor
- Test route decision
