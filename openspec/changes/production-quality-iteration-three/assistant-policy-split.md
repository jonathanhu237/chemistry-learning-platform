# Assistant Policy Split

Date: 2026-06-17

## Scope

The third-pass assistant slice moved deterministic policy and request-classification logic out of `server/app/agent.py` into `server/app/services/agent_policy.py`.

Moved responsibilities:

- course/out-of-scope/resource/assessment/safety keyword sets
- `AgentPolicy`
- `load_agent_policy`
- source-asset and platform-resource request detection
- intent naming
- `classify_agent_request`
- policy mode constants

`server/app/agent.py` still re-exports/imports `AgentPolicy`, `load_agent_policy`, and `classify_agent_request`, so existing endpoint code and tests that import these names from `server.app.agent` remain compatible.

## Characterization

Added tests around:

- source figure requests staying on the learning/RAG evidence rail
- platform resource availability requests requiring published-resource evidence

## Verification

- `python -m pytest server\tests\test_student_chat_image_evidence.py -q`: PASS, 4 passed
- `python -m pytest server\tests\test_student_chat_image_evidence.py server\tests\test_student_chat_guardrails.py server\tests\test_assistant_runtime_characterization.py -q`: PASS, 15 passed
- `python -m pytest server\tests -q`: PASS, 52 passed
- `python -c "import server.app.agent as a; print(a.AgentPolicy.__name__, a.classify_agent_request.__name__, a.run_agent.__name__)"`: PASS

Line count after extraction:

- `server/app/agent.py`: 1090 lines
- `server/app/services/agent_policy.py`: 243 lines
