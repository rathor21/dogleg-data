# Dogleg Data

Golf analytics content site (github.com/rathor21/dogleg-data): numbered data-driven analyses (`analysis/<NNN>-<topic>/`) turned into a static site (`site/`), plus brand and launch material (`brand/`, `launch/`).

## Existing reference docs

- **Design system**: `.impeccable.md` — brand personality, design tokens, reference implementation.
- **Brand spec**: `Dogleg_Data_Brand_Spec.md`.
- **Launch strategy**: `Dogleg_Data_Launch_Strategy.md`, `launch/Launch_Day_Kit.md`, `launch/Launch_Plan_Monday_Jul6.md`.
- **Per-analysis plans and peer review**: `docs/plans/`, `docs/sources/`.

## Agent skills

### Issue tracker

Issues live as GitHub issues in this repo (rathor21/dogleg-data); skills use the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

Default label vocabulary: needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context layout — one `CONTEXT.md` + `docs/adr/` at the repo root (not created yet; `/domain-modeling` writes these lazily when concepts actually get resolved). See `docs/agents/domain.md`.
