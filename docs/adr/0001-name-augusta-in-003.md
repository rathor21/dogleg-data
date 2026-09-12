# ADR 0001: Release 003 names Augusta National throughout

Date: 2026-08-13 · Status: accepted · Decider: Sunny

## Context

Release 003 models tee-shot aim strategy on the 12th hole at Augusta National. During scoping, Claude recommended a split posture: name the hole in article text (editorial fact reporting) while keeping the title, URL slug, social cards, and rendered scenes free of Augusta branding, because detached shareable assets are what a rights-holder screenshots, and Augusta National enforces its marks harder than any club in golf.

## Decision

Sunny chose full nominative use. The title, slug, social cards, animation labels, and article all name Augusta National and the Masters outright. Rationale: Dogleg Data is small, non-commercial, and below any enforcement threshold; the recognition value of the name is central to the piece's reach.

One boundary holds regardless: no Augusta-owned photography or broadcast frames appear anywhere in the piece. That line is copyright, small-site obscurity does not defend it, and the piece renders its own stylized hole from published yardage-book geometry.

## Consequences

- Headlines and social assets get the full pull of the most recognizable venue in golf.
- The piece carries a nonzero takedown risk that the split posture would have reduced. Accepted with open eyes.
- If a complaint ever arrives, the fallback is the split posture: retitle, re-slug, strip marks from shareable assets, keep the article text. The model and animation survive unchanged.
- The rendering pipeline must stay self-sourced: geometry from published yardage books and pin sheets, no traced photographs.
