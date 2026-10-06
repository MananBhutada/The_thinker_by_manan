# Changelog

## v1.1.0 - Graph-first workspace

### Added

- Intro page at `/` with an animated founder-graph preview; the first thought typed there is handed to the workspace at `/app`.
- Lenses (Brain, Money, Product, People, Risk, Evidence, Sequence, Future), graph search (`/`), and an Insights drawer with Insights, Funnel and Shape tabs. All derived from the stored graph by the new `frontend/scripts/insights.js`.
- Importance tiers (core / support / peripheral) from degree and betweenness, soft cluster halos with labels, global node repulsion, and a richer hover tooltip.
- Node-level highlight from insights and funnel stages, with a Clear control.
- `tests/frontend/insights.test.js` and `tests/test_landing_routes.py`.

### Fixed

- Selecting a node dimmed *every* node, including the selected one: `is-sel` / `is-nb` were styled but never applied.
- A removed or merged node could leave a stale selection and coach panel behind; the workspace now clears both.
- Closing the coach panel did not restore the graph's inset because insets were merged, not replaced.
- `map.html` carried an inline script that the CSP blocks; it is now identical to `index.html`.
- README, package name and description described the old BlindSpot app.

## v0.9.1 - 2026-08-17

### Changed

- Consolidated the installable Agent Skill under `skills/choice-assistant/` and removed the duplicate repository-root entry.
- Added a deterministic Skill package builder and validator, with a versioned ZIP and SHA-256 checksum as release assets.
- Aligned the README navigation, release status, Pages JSON-LD, sitemap, and `llms.txt` with the `v0.9.1` identity.
- Split backend tests from the Playwright desktop job; CI now starts the backend and installs Chromium before UI checks.
- Aligned the Yao manifest and interface across OpenAI, Claude, Generic, Agent Skills, and VS Code targets.

## v0.9.0 - 2026-07-26

### Added

- Four switchable interface styles: Heritage, Quiet Workbench, Decision Journal, and Modular Console.
- Six browser-rendered random effects: pointer draw, fortune sticks, 3D dice, six-card draw, ticket machine, and ink path.
- Richer Nature evidence including location, temperature, humidity, wind, daylight, moon phase, forecast, alerts, air information, and signal weights.
- Dialogue answer history persisted as question-and-answer pairs in `dialogueHistory`.
- User-managed Amap weather Key, Base URL, and city settings in both Web and CLI flows.
- Detailed Chinese and English feature maps and module-level project structure documentation.
- Updated Chinese and English intro animations with the Mini Program logo, four interface styles, and six random effects.

### Changed

- Reused the Mini Program logo in the open-source desktop interface.
- Renamed the user-facing Fengshui label to Traditional Culture while keeping the internal `fengshui` id for compatibility.
- Reworked the random result presentation and added a standalone effect preview page.
- Nature mode now uses live Amap data only when both Key and Base URL are configured; otherwise it clearly labels simulated weather.
- Removed the previously embedded weather credential and corrected public documentation that described weather as built in.
- Updated repository discovery metadata and added a downloadable source archive to the Release.

### Fixed

- Dialogue option clicks now save the selected answer instead of sending an unused completion flag.
- Weather settings no longer show the bare label "simulated data" without explaining when it is used.
- Static asset versions were bumped so updated settings and translations are not hidden by browser cache.

### Verification

- `87 passed, 15 skipped` in the full pytest suite.
- `15 passed` in the desktop Playwright suite.
- Browser console clean; desktop settings and random effect layouts checked without horizontal overflow.

## v0.8.4 - 2026-07-07

### Added

- Local-first decision archive with Web UI and CLI access.
- Six decision lenses: Auto, Rational, Random, Nature, Dialogue, and Fengshui.
- Multimodal input support for text, voice, and image-based decision context.
- Internationalized UI with Chinese and English README files.
- TTS, browser speech input, weather context, archive, statistics, and mock fallback mode.
- Public repository materials: disclaimer, acknowledgements, security policy, contribution guide, and GitHub templates.

### Notes

- This project is decision-support software, not professional advice.
- Users should read `DISCLAIMER.md` before using it for personal or high-stakes decisions.