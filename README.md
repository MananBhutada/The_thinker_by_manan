# BlindSpot AI

BlindSpot AI is an AI-powered decision reflection tool that helps people identify blind spots in their reasoning before acting.

It does **not** choose for the user. Instead, it stress-tests a decision by surfacing assumptions, overlooked factors, conflicting priorities, uncertainty, missing information, and useful follow-up questions.

## Why BlindSpot AI?

People often evaluate a decision from the perspective they already prefer. BlindSpot AI deliberately introduces friction into that reasoning process:
- **Assumptions** — What are you taking for granted?
- **Blind spots** — What important factor might be missing from the current framing?
- **Trade-offs** — What does each option improve, and what does it cost?
- **Conflicts** — Which goals or values are pulling in opposite directions?
- **Missing information** — What should you verify before committing?
- **Reflection questions** — What question would most improve the quality of the decision?

## How it works

1. The user describes a decision in natural language.
2. The system routes the request through a decision-analysis mode.
3. AI analyzes the reasoning from multiple perspectives instead of producing a simple recommendation.
4. The result is presented as a structured decision brief.
5. The user keeps full ownership of the final decision.

## Current modes

| Mode | Purpose |
| --- | --- |
| **Auto** | Select the most useful analysis approach automatically. |
| **Reason** | Examine benefits, risks, trade-offs, reversibility, and opportunity cost. |
| **Random** | Use randomness as a reflection device for low-stakes choices, not as evidence. |
| **Nature** | Add current environmental context as an alternative perspective. |
| **Dialogue** | Ask reflective questions that help expose the user's own reasoning. |
| **Traditional** | Provide a clearly labeled traditional-culture perspective for reflection only. |

## Tech stack

- **Backend:** Python, FastAPI, SQLite, Pydantic, HTTPX
- **Frontend:** HTML, CSS, JavaScript with no build step
- **AI:** Any OpenAI-compatible chat-completions API
- **Speech:** Browser Speech API and optional Edge TTS
- **Testing:** pytest and Playwright

## Run locally

    pip install -r requirements.txt
    cd backend
    python main.py

Then open `http://127.0.0.1:8010/`.

For real AI analysis, configure an OpenAI-compatible API key through the application settings or environment variables. Without a key, the application can run in Demo mode with clearly labeled mock results.

## Environment variables

    CHOICE_LLM_API_KEY=your_api_key
    CHOICE_LLM_MODEL=gpt-4o-mini
    CHOICE_LLM_BASE_URL=https://api.openai.com/v1

## Safety and boundaries

BlindSpot AI is a decision-support tool, not an autonomous decision-maker. It should not replace qualified professional advice for medical, legal, financial, employment, or other high-stakes decisions.

AI output can be incomplete or wrong. The purpose of the system is to improve the user's reasoning process, not to create false certainty.

## Repository structure

- `frontend/` — web interface and client-side rendering
- `backend/` — FastAPI application, routing, AI services, and persistence
- `scripts/` — CLI and packaging utilities
- `tests/` — automated tests
- `docs/` — documentation and demo assets
- `skills/choice-assistant/` — bundled decision-support skill

## License

MIT. See [LICENSE](LICENSE).

---

Built as a hackathon prototype for **THE BLIND SPOT**: help people see what their reasoning may be missing before they decide.