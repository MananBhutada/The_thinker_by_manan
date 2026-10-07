# FounderOS

**For founders whose brains move faster than their roadmap.**

FounderOS turns a messy dump of founder thinking into a living network of ideas, decisions, money, people, products, risks, assumptions and unknowns. The graph is the product. AI is contextual help around it: it extracts, connects and questions, but it never decides for you and never turns a guess into a fact.

## What you get

| Surface | What it does |
| --- | --- |
| `/` Intro page | Explains the idea in ten seconds, previews the graph, and hands your first thought to the workspace. |
| `/app` Workspace | A force-directed founder graph: curved edges, importance-sized nodes, emergent clusters, drag / zoom / pan, hover and selection neighbourhoods. |
| Contextual coach | Click any node and chat. The model receives that node's graph context (parents, cross-links, assumptions, evidence, capital), not just its title. |
| Lenses | Brain · Money · Product · People · Risk · Evidence · Sequence · Future. Same graph, different emphasis. |
| Search | Press `/`. Matches highlight, neighbours stay visible, everything else dims. Enter opens the coach on the first match. |
| Insights | Graph-derived questions: structural gaps, orphaned ideas, overloaded nodes, unresolved dependencies, untested assumptions, loose thoughts. Always phrased as questions. |
| Funnel | Where your thinking sits (thought, question, assumption, evidence, experiment, decision, commitment), computed from node type and state. Nothing is estimated. |
| Shape | Bridge nodes, clusters, evidence coverage, and "Explore periphery". |

AI-proposed blind spots are visibly distinct (dotted, labelled) and stay proposals until you Accept, Ignore or Reject them. A question you ask yourself is founder context, not an AI proposal.

## Architecture

- **Backend:** FastAPI. Graph API in `backend/routes/graph.py`, extraction / merge / node-context in `backend/services/graph_service.py`.
- **Workspace isolation:** a signed `founderos_workspace` cookie scopes every persisted record. PostgreSQL is the only runtime datastore, with graph documents stored as JSONB and decisions/config scoped by workspace. Authentication can later map a user account to one or more workspace IDs without changing the storage boundary.
- **LLM:** any OpenAI-compatible endpoint. The hosted "Free AI" path uses OpenRouter with a primary model plus fallbacks, and a deterministic extractor keeps *Map* working if the model is unreachable. Keys stay server-side or are used per request (BYOK) and never stored.
- **Frontend:** plain HTML / CSS / JS, no build step. `graph.js` (SVG force layout), `insights.js` (pure analytics, unit-testable in Node), `workspace.js` (UI), `landing.js`.
- **CSP:** `script-src 'self'`. No inline scripts anywhere.

## Run locally

    pip install -r requirements.txt
    cd backend
    python main.py

Open `http://127.0.0.1:8010/`.

## Configuration

| Variable | Purpose |
| --- | --- |
| `FOUNDEROS_FREE_AI_API_KEY` | Key for the hosted Free AI path (server-side only). |
| `FOUNDEROS_FREE_AI_MODEL` / `_BASE_URL` / `_FALLBACK_MODELS` | Override the default model, endpoint and fallbacks. |
| `FOUNDEROS_SESSION_SECRET` | Signs workspace cookies. **Set this in production.** |
| `DATABASE_URL` | **Required.** PostgreSQL connection string for the application datastore. |

## PostgreSQL setup

FounderOS now requires PostgreSQL at runtime.

For local development, create a PostgreSQL database and export its connection string:

    export DATABASE_URL="postgresql://USER:PASSWORD@HOST:5432/founderos"

The API creates/updates its schema automatically on startup. PostgreSQL JSONB is used for the current graph document so the existing graph API remains compatible while the storage layer is prepared for future normalized entities and authentication.

If an existing deployment still has `backend/choice.db`, migrate it before switching the service to PostgreSQL:

    DATABASE_URL="postgresql://USER:PASSWORD@HOST:5432/founderos" \
      python scripts/migrate_sqlite_to_postgres.py

The migration preserves every existing graph `workspace_id`. Legacy decisions and config, which did not previously have workspace ownership, are imported into the `local` workspace.

On Render, set the service's `DATABASE_URL` to the PostgreSQL database connection string. Render Blueprints can also wire a Postgres database's `connectionString` directly into `DATABASE_URL`.

## Tests

    node tests/frontend/insights.test.js      # graph analytics, lenses, funnel
    python -m pytest tests/test_landing_routes.py

## Credits and licence

MIT. See [LICENSE](LICENSE) and [ACKNOWLEDGEMENTS.md](ACKNOWLEDGEMENTS.md) for upstream copyright and the projects this builds on.