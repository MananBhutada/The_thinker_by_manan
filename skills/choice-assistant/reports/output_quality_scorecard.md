# Output quality scorecard

Release candidate: `v0.9.1`

This scorecard defines the evidence expected for the installable Skill. It does not claim live third-party model quality or automatic activation telemetry.

| Gate | Evidence | Boundary |
| --- | --- | --- |
| Package integrity | `scripts/validate_package.py` | Exactly one package-root `SKILL.md`, required runtime files, no private paths or local databases |
| Skill conformance | `agentskills validate skills/choice-assistant` | Valid frontmatter and installable Skill directory shape |
| CLI reachability | `python scripts/choice_assistant.py --help` | Help renders without contacting a backend or requiring credentials |
| Trigger boundary | `evals/trigger-cases.yaml` | Decision-support prompts trigger; translation, general knowledge, and guaranteed high-stakes advice do not |
| Output contract | `SKILL.md` and API tests | Summary, confidence, perspectives, risks, next steps, mode, source, and optional `decisionId` |
| Human review | `README.md`, `DISCLAIMER.md`, `SECURITY.md` | Users remain responsible for professional and high-stakes decisions |

Missing evidence by design: live LLM/provider comparison, automatic activation rate, GitHub ranking, and human adoption telemetry.
