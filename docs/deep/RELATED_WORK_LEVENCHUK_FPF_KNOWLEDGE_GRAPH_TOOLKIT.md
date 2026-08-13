# Related work: Levenchuk's FPF Knowledge Graph Toolkit (anatoly-m-maslennikov fork)

**Status**: Acknowledged — inspected, rejected entirely, nothing incorporated.
**Date**: 2026-08-13
**Decision by**: igareosh (prichindel.com)
**Related repo**: [anatoly-m-maslennikov/levenchuk-fpf-knowledge-graph-toolkit](https://github.com/anatoly-m-maslennikov/levenchuk-fpf-knowledge-graph-toolkit)
**FPF source repo**: [ailev/FPF](https://github.com/ailev/FPF)
**Trigger**: [ailev/FPF PR #49](https://github.com/ailev/FPF/pull/49) ("Am/dev"), opened 2026-08-03 by anatoly-m-maslennikov, closed unmerged 2026-08-12.

---

## What we found

A fork of `ailev/FPF` that never merged back. Its author proposed splitting the flat ~103k-line `FPF-Spec.md` into a generated Obsidian vault (341 files: hubs, indexes, wikilinked ids) plus a CI workflow and a bundle of `SKILL.md`-format agent skills, submitted as PR #49 against upstream `main`. The PR sat with zero reviews and zero comments for 9 days, then was closed unmerged. Upstream `ailev/FPF` main is still a single flat file today, continuing ailev's own small hand-edits (`036c056`, 2026-08-08, and later). The fork itself lives on independently — actively developed as recently as 2026-08-12 under its current name, unrelated to whether upstream took it.

We verified the generator's fidelity claim rather than trusting it: diffed one full pattern (`A.1`, 356 lines) from the commit both repos share (`9a9a42e`) against the fork's generated file. The prose is untouched — every diff line is a mechanical id-to-wikilink substitution or a heading-level shift, nothing rewritten. That part of the claim holds up.

## What it builds

A **prompt-time skill bundle**, not an engine. Eight `SKILL.md` packages (`fpf-route`, `fpf-applicability-scan`, `fpf-design-challenge`, `fpf-alignment-audit`, `fpf-sota-harvest`, `fpf-options-explore`, `fpf-decision-synthesize`, `fpf-quality-improve`) instruct a model to read bounded FPF pattern pages, then self-report a verdict (per-skill vocabularies such as `boundedly supported` / `unsupported` / `insufficient basis`) and a per-claim confidence band (`>=95%` high-confidence, `90-94%` probable, `<90%` uncertain) inside a mandatory "result envelope" — assembled by the same completion whose own claims it is grading.

No code evaluates anything. The confidence band, the verdict, and the "skills used" self-report are all generated in the same forward pass as the claim they describe. There is no independent check — deterministic or adversarial — anywhere in the loop.

## Why rejected

Same core objection already on record in `RELATED_WORK_GOFLOW_FPF_SKILL.md`: this package's premise is that a model should not be trusted to grade its own reasoning, because reasoning-about-reasoning is exactly where a model hallucinates most confidently and fluently. This toolkit doesn't just risk that failure mode — it is built entirely out of it. A "High-confidence results (>=95%)" heading is not a check; it is the model narrating itself into a shape that reads as rigor. That is worse than no envelope at all: a plain uncertain answer looks uncertain, a self-graded 97% inside a formatted section looks verified. Nothing in it has an externally checkable answer to grade against, at any layer.

The one structurally reusable idea — `fpf-route`'s task taxonomy (applicability-scan -> design-challenge/alignment-audit -> decision-synthesize -> quality-improve) as a routing shape for *which* workflow a task needs — isn't worth extracting either: it is thin enough to derive from scratch if a real need for it ever shows up. Neither `ailev/FPF` nor this fork carry a declared license (`licenseInfo: null` on both, checked directly against the GitHub API), so the `SKILL.md` prose itself isn't safe to lift verbatim regardless.

## Conclusion

Acknowledged, inspected, nothing incorporated. No engine to compare against ours — it is a prompt-convention layer with no deterministic or adversarial verification anywhere, built on top of a spec-restructuring PR that upstream ignored and closed. Filed for the record, same as the goflow entry, so the next person who finds this fork doesn't have to re-derive the same evaluation.

---

prichindel.com | 2026-08-13 | v1.9.5
